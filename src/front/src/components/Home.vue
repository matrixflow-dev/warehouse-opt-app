<template>
    <div>
        <b-row class="justify-content-center">
            <b-col cols="10">
                <b-alert :show="errorMessage !== null" variant="danger" dismissible @dismissed="errorMessage = null">
                    {{ errorMessage }}
                </b-alert>
            </b-col>
        </b-row>

        <b-row class="justify-content-center">
            <b-col cols="5">
                <b-form-group label="ピッカー">
                    <b-form-select v-model="selectedAgents" multiple>
                        <b-form-select-option v-for="agent in agentOptions" :key="agent" :value="agent">
                            {{ agent }}
                        </b-form-select-option>
                    </b-form-select>
                </b-form-group>
            </b-col>

            <b-col cols="5">
                <b-form-group label="マップ情報">
                    <b-form-select v-model="selectedMapConfig">
                        <b-form-select-option v-for="config in mapConfigOptions" :key="config.id" :value="config.id">
                            {{ config.name }}
                        </b-form-select-option>
                    </b-form-select>
                </b-form-group>
            </b-col>
        </b-row>

        <b-row class="justify-content-center">
            <b-col cols="5">
                <b-form-group label="在庫情報">
                    <b-form-select v-model="selectedStock">
                        <b-form-select-option v-for="stock in stockOptions" :key="stock.id" :value="stock.id">
                            {{ stock.id }} - {{ stock.created_at }}
                        </b-form-select-option>
                    </b-form-select>
                </b-form-group>
            </b-col>

            <b-col cols="5">
                <b-form-group label="ピッキングリスト">
                    <b-form-select v-model="selectedPickingList">
                        <b-form-select-option v-for="list in pickingListOptions" :key="list" :value="list">
                            {{ list }}
                        </b-form-select-option>
                    </b-form-select>
                </b-form-group>
            </b-col>
        </b-row>

        <b-row class="justify-content-center">
            <b-button :disabled="loading" variant="primary" @click="sendRequest">
                <span v-if="loading"><b-spinner small></b-spinner>解析中</span>
                <span v-else>解析開始</span>
            </b-button>
        </b-row>
        <b-row class="justify-content-center">
            <b-button v-show="resultId" variant="primary" @click="downloadZip">
                結果をダウンロードする
            </b-button>
        </b-row>

        <b-row class="justify-content-center">
            <img :src="gifSrc" alt="GIF" v-if="gifSrc" />
        </b-row>
    </div>
</template>

<script>
import axios from 'axios';

export default {
    name: 'Main',
    data() {
        return {
            agentOptions: [],
            mapConfigOptions: [],
            stockOptions: [],
            pickingListOptions: [],
            selectedAgents: [],
            selectedMapConfig: '',
            selectedStock: '',
            selectedPickingList: '',
            loading: false,
            gifSrc: null,
            resultId: null,
            errorMessage: null
        };
    },
    methods: {
        fetchOptions() {
            Promise.all([
                axios.get('/api/agents'),
                axios.get('/api/map-configs'),
                axios.get('/api/stocks'),
                axios.get('/api/picking-lists')
            ]).then(([agentsRes, mapConfigsRes, stocksRes, pickingListsRes]) => {
                this.agentOptions = agentsRes.data;
                this.mapConfigOptions = mapConfigsRes.data.mapConfigs; // mapConfigs配列を取得
                this.stockOptions = stocksRes.data.stocks;
                this.pickingListOptions = pickingListsRes.data;
            }).catch(error => {
                this.errorMessage = '予期せぬエラーが発生しました。管理者に問い合わせてください: ' + error.message;
            });
        },
        sendRequest() {
            this.resultId = null;
            this.loading = true;
            this.errorMessage = null;

            const payloadStart = {
                agent_ids: this.selectedAgents,
                map_config_id: this.selectedMapConfig,
                stock_id: this.selectedStock,
                picking_list_id: this.selectedPickingList
            };

            axios.post('/api/start', payloadStart)
                .then(responseStart => {
                    this.resultId = responseStart.data.result_id;

                    const payloadViz = {
                        agent_ids: this.selectedAgents,
                        map_config_id: this.selectedMapConfig,
                        stock_id: this.selectedStock,
                        picking_list_id: this.selectedPickingList,
                        result_id: this.resultId
                    };
                    return axios.post('/api/visualize', payloadViz);
                })
                .then(response => {
                    this.gifSrc = `data:image/gif;base64,${response.data.gif}`;
                })
                .catch(error => {
                    this.errorMessage = '予期せぬエラーが発生しました。管理者に問い合わせてください: ' + error.message;
                    console.log(this.errorMessage);
                })
                .finally(() => {
                    this.loading = false;
                });
        },
        downloadZip() {
            axios.get(`/api/download/${this.resultId}`, {
                responseType: 'blob'
            }).then(response => {
                const contentDisposition = response.headers['content-disposition'];
                let filename = this.resultId + '.zip';
                if (contentDisposition) {
                    const filenameMatch = contentDisposition.match(/filename="(.+)"/);
                    if (filenameMatch && filenameMatch.length > 1) {
                        filename = filenameMatch[1];
                    }
                }

                const url = window.URL.createObjectURL(new Blob([response.data]));
                const link = document.createElement('a');
                link.href = url;
                link.setAttribute('download', filename);
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            }).catch(error => {
                this.errorMessage = '予期せぬエラーが発生しました。管理者に問い合わせてください: ' + error.message;
            });
        }
    },
    mounted() {
        this.fetchOptions();
    }
};
</script>