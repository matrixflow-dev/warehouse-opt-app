<template>
    <div>
        <b-row>
            <b-col cols="10">
                <b-alert :show="errorMessage !== null" variant="danger" dismissible @dismissed="errorMessage = null">
                    {{ errorMessage }}
                </b-alert>
            </b-col>
        </b-row>

        <b-row>
            <b-col cols="6">
                <b-form-group label="ピッカーグループ">
                    <b-form-select v-model="selectedAgents">
                        <b-form-select-option v-for="agent in agentOptions" :key="agent.id" :value="agent.id">
                            {{ agent.name }}
                        </b-form-select-option>
                    </b-form-select>
                </b-form-group>
            </b-col>

            <b-col cols="6">
                <b-form-group label="マップ情報">
                    <b-form-select v-model="selectedMapConfig">
                        <b-form-select-option v-for="config in mapConfigOptions" :key="config.id" :value="config.id">
                            {{ config.name }}
                        </b-form-select-option>
                    </b-form-select>
                </b-form-group>
            </b-col>
        </b-row>

        <b-row>
            <b-col cols="6">
                <b-form-group label="在庫情報">
                    <b-form-select v-model="selectedStock">
                        <b-form-select-option v-for="stock in stockOptions" :key="stock.id" :value="stock.id">
                            {{ stock.name }} - {{ stock.created_at }}
                        </b-form-select-option>
                    </b-form-select>
                </b-form-group>
            </b-col>

            <b-col cols="6">
                <b-form-group label="ピッキングリスト">
                    <b-form-select v-model="selectedPickingList">
                        <b-form-select-option v-for="list in pickingListOptions" :key="list.id" :value="list.id">
                            {{ list.name }} - {{ list.created_at }}
                        </b-form-select-option>
                    </b-form-select>
                </b-form-group>
            </b-col>
        </b-row>

        <b-row>
            <b-button :disabled="loading" variant="primary" @click="sendRequest">
                <span v-if="loading"><b-spinner small></b-spinner>解析中</span>
                <span v-else>解析開始</span>
            </b-button>
        </b-row>

        <b-row class="mt-2">
            <b-button v-show="resultId" variant="primary" @click="downloadZip">
                結果をダウンロードする
            </b-button>
        </b-row>

        <!-- グラフとGIFを横並びに表示 -->
        <b-row class="mt-4">
            <b-col cols="6">
                <b-row>
                    <b-col cols="6">
                        <canvas id="makespanChart"></canvas>
                    </b-col>
                    <b-col cols="6">
                        <canvas id="avgStepsChart"></canvas>
                    </b-col>
                </b-row>
                <b-row class="mt-4">
                    <b-col cols="12">
                        <canvas id="agentsChart"></canvas>
                    </b-col>
                </b-row>
            </b-col>

            <b-col cols="6">
                <b-row class="justify-content-center">
                    <span v-if="loadingViz" style="color:#850491;">
                        <b-spinner class="big-spinner"></b-spinner>行動可視化準備中
                    </span>
                    <span v-else>
                        <img :src="gifSrc" alt="GIF" v-if="gifSrc" style="width:100%" />
                    </span>
                </b-row>
            </b-col>
        </b-row>
    </div>
</template>

<script>
import axios from 'axios';
import Chart from 'chart.js/auto';

export default {
    name: 'Main',
    data() {
        return {
            agentOptions: [],
            mapConfigOptions: [],
            stockOptions: [],
            pickingListOptions: [],
            selectedAgents: "",
            selectedMapConfig: '',
            selectedStock: '',
            selectedPickingList: '',
            loading: false,
            loadingViz: false,
            gifSrc: null,
            resultId: null,
            errorMessage: null,
            maxSteps: 0,
            avgSteps: 0,
            eachStepsList: [],
            charts: {}, // 複数のチャートを保持するためのオブジェクト
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
                this.agentOptions = agentsRes.data.agents;
                this.mapConfigOptions = mapConfigsRes.data.mapConfigs;
                this.stockOptions = stocksRes.data.stocks;
                this.pickingListOptions = pickingListsRes.data.pickingLists;
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
                    this.loading = false;
                    this.loadingViz = true;
                    this.resultId = responseStart.data.result_id;

                    this.maxSteps = responseStart.data.makespan;
                    this.avgSteps = responseStart.data.avg_steps;
                    this.eachStepsList = responseStart.data.agents;

                    this.renderCharts(); // チャートを描画

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
                    this.loadingViz = false;
                });
        },
        renderCharts() {
            // 既存のチャートがあれば破棄
            if (this.charts.makespanChart) this.charts.makespanChart.destroy();
            if (this.charts.avgStepsChart) this.charts.avgStepsChart.destroy();
            if (this.charts.agentsChart) this.charts.agentsChart.destroy();

            // Makespanのチャート
            const makespanCtx = document.getElementById('makespanChart').getContext('2d');
            this.charts.makespanChart = new Chart(makespanCtx, {
                type: 'bar',
                data: {
                    labels: ['Makespan'],
                    datasets: [{
                        label: 'Makespan',
                        data: [this.maxSteps],
                        backgroundColor: 'rgba(54, 162, 235, 0.2)',
                        borderColor: 'rgba(54, 162, 235, 1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });

            // 平均ステップ数のチャート
            const avgStepsCtx = document.getElementById('avgStepsChart').getContext('2d');
            this.charts.avgStepsChart = new Chart(avgStepsCtx, {
                type: 'bar',
                data: {
                    labels: ['Average Steps'],
                    datasets: [{
                        label: 'Average Steps',
                        data: [this.avgSteps],
                        backgroundColor: 'rgba(255, 159, 64, 0.2)',
                        borderColor: 'rgba(255, 159, 64, 1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });

            // 各エージェントのステップ数のチャート
            const agentsCtx = document.getElementById('agentsChart').getContext('2d');
            this.charts.agentsChart = new Chart(agentsCtx, {
                type: 'bar',
                data: {
                    labels: Object.keys(this.eachStepsList).map(key => `Agent ${key}`),
                    datasets: [{
                        label: 'Steps',
                        data: Object.values(this.eachStepsList),
                        backgroundColor: 'rgba(75, 192, 192, 0.2)',
                        borderColor: 'rgba(75, 192, 192, 1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
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
<style>
.big-spinner {
    width: 2rem;
    height: 2rem;
    color: #850491;
}
</style>