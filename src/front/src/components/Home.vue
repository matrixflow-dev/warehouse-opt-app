<template>
    <div>
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
                        <b-form-select-option v-for="config in mapConfigOptions" :key="config" :value="config">
                            {{ config }}
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
            resultId: null
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
                this.mapConfigOptions = mapConfigsRes.data;
                this.stockOptions = stocksRes.data.stocks;
                this.pickingListOptions = pickingListsRes.data;
            }).catch(error => {
                console.error('Error fetching options:', error);
            });
        },
        sendRequest() {
            this.loading = true;
            const payloadStart = {
                agent_ids: this.selectedAgents,
                map_config_id: this.selectedMapConfig,
                stock_id: this.selectedStock,
                picking_list_id: this.selectedPickingList
            };

            axios.post('/api/start', payloadStart)
                .then(responseStart => {
                    console.log('Response:', responseStart.data);
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
                    console.log('Response:', response.data);
                    this.gifSrc = `data:image/gif;base64,${response.data.gif}`;
                })
                .catch(error => {
                    console.error('Error sending request:', error);
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
                let filename = this.zipId + '.zip';
                if (contentDisposition) {
                    const filenameMatch = contentDisposition.match(/filename="(.+)"/);
                    if (filenameMatch.length > 1) {
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
                console.error("Error downloading the ZIP file:", error);
            });
        }
    },
    mounted() {
        this.fetchOptions();
    }
};
</script>