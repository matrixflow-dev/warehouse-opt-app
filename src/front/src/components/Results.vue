<template>
    <div>
        <h1>結果</h1>
        <p>結果を表示します。</p>

        <!-- テーブル -->
        <b-table :items="results" :fields="fields" @row-clicked="onRowClicked">
            <!-- テーブルの内容はそのまま -->
        </b-table>

        <b-pagination v-model="currentPage" :total-rows="totalResults" :per-page="perPage" @change="fetchResults"
            aria-controls="results-table"></b-pagination>

        <!-- 詳細モーダル -->
        <b-modal v-if="selectedResult" @hide="selectedResult = null" @shown="onModalShown" title="結果詳細"
            :visible="showModal" modal-class="custom-modal">
            <p><strong>ID:</strong> {{ selectedResult.result_id }}</p>
            <p><strong>作成日時:</strong> {{ selectedResult.created_at }}</p>
            <p><strong>最大時間:</strong> {{ selectedResult.makespan }}</p>
            <p><strong>ピッカーグループ:</strong> {{ selectedResult.req_params.agent.name }} - {{
            selectedResult.req_params.agent.created_at }}</p>
            <p><strong>在庫情報:</strong> {{ selectedResult.req_params.stock.name }} - {{
            selectedResult.req_params.stock.created_at }}</p>
            <p><strong>ピッキングリスト:</strong> {{ selectedResult.req_params.picking_list.name }} - {{
            selectedResult.req_params.picking_list.created_at }}</p>
            <p><strong>マップ情報:</strong> {{ selectedResult.req_params.map_config.name }}</p>

            <!-- グラフとGIFを横並びに表示 -->
            <b-row class="mt-4">
                <b-col cols="6">
                    <b-row>
                        <b-col cols="6">
                            <canvas id="makespanChartModal"></canvas>
                        </b-col>
                        <b-col cols="6">
                            <canvas id="avgStepsChartModal"></canvas>
                        </b-col>
                    </b-row>
                    <b-row class="mt-4">
                        <b-col cols="12">
                            <canvas id="agentsChartModal"></canvas>
                        </b-col>
                    </b-row>
                </b-col>

                <b-col cols="6">
                    <b-row class="justify-content-center">
                        <span v-if="loadingViz" style="color:#850491;">
                            <b-spinner class="big-spinner"></b-spinner>行動可視化準備中
                        </span>
                        <span v-else>
                            <img :src="gifSrc" alt="GIF" v-if="gifSrc" style="width:60%" />
                        </span>
                    </b-row>
                </b-col>
            </b-row>

            <b-row>
                <b-button v-show="resultId" variant="primary" @click="downloadZip">
                    結果をダウンロードする
                </b-button>
            </b-row>

            <!-- フッター -->
            <template #modal-footer>
                <div class="d-flex justify-content-between w-100">
                    <b-button variant="danger" @click="deleteResult" class="mt-3">削除</b-button>
                    <b-button @click="showModal = false" class="mt-3">閉じる</b-button>
                </div>
            </template>
        </b-modal>
    </div>
</template>

<script>
import axios from 'axios';
import Chart from 'chart.js/auto';

export default {
    name: 'Results',
    data() {
        return {
            results: [],
            totalResults: 0,
            fields: [
                { key: 'result_id', label: 'ID' },
                { key: 'created_at', label: '作成日時' },
                { key: 'makespan', label: '最大時間' },
                { key: 'picker_group', label: 'ピッカーグループ' },
                { key: 'stock_info', label: '在庫情報' },
                { key: 'picking_list', label: 'ピッキングリスト' },
                { key: 'map_info', label: 'マップ情報' },
            ],
            currentPage: 1,
            perPage: 10,
            selectedResult: null,
            showModal: false,
            loadingViz: false,
            gifSrc: null,
            resultId: null,
            maxSteps: 0,
            avgSteps: 0,
            eachStepsList: [],
            charts: {},
        };
    },
    mounted() {
        this.fetchResults();
    },
    methods: {
        fetchResults() {
            const offset = (this.currentPage - 1) * this.perPage;
            const limit = this.perPage;

            axios.get('/api/results', {
                params: { offset, limit }
            })
                .then(response => {
                    this.results = response.data.results;
                    this.totalResults = response.data.total;
                })
                .catch(error => {
                    console.error('結果情報の取得に失敗しました:', error);
                });
        },
        onRowClicked(item) {
            axios.get(`/api/results/${item.result_id}`)
                .then(response => {
                    this.selectedResult = response.data.result;
                    this.resultId = item.result_id;
                    this.maxSteps = this.selectedResult.makespan;
                    this.avgSteps = this.selectedResult.avg_steps || 0;
                    this.eachStepsList = this.selectedResult.agents || [];
                    this.showModal = true;
                    this.loadVisualization(this.selectedResult.gif);
                })
                .catch(error => {
                    console.error('詳細情報の取得に失敗しました:', error);
                });
        },
        onModalShown() {
            this.renderCharts();
        },
        deleteResult() {
            if (!this.selectedResult) return;

            axios.delete(`/api/results/${this.selectedResult.result_id}`)
                .then(() => {
                    this.showAlert('結果が削除されました。', 'success');
                    this.fetchResults();
                    this.selectedResult = null;
                    this.showModal = false;
                })
                .catch(error => {
                    console.error('結果の削除に失敗しました:', error);
                    this.showAlert('結果の削除に失敗しました。', 'danger');
                });
        },
        renderCharts() {
            if (this.charts.makespanChartModal) this.charts.makespanChartModal.destroy();
            if (this.charts.avgStepsChartModal) this.charts.avgStepsChartModal.destroy();
            if (this.charts.agentsChartModal) this.charts.agentsChartModal.destroy();

            const makespanCtx = document.getElementById('makespanChartModal').getContext('2d');
            this.charts.makespanChartModal = new Chart(makespanCtx, {
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
                        y: { beginAtZero: true }
                    }
                }
            });

            const avgStepsCtx = document.getElementById('avgStepsChartModal').getContext('2d');
            this.charts.avgStepsChartModal = new Chart(avgStepsCtx, {
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
                        y: { beginAtZero: true }
                    }
                }
            });

            const agentsCtx = document.getElementById('agentsChartModal').getContext('2d');
            this.charts.agentsChartModal = new Chart(agentsCtx, {
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
                        y: { beginAtZero: true }
                    }
                }
            });
        },
        loadVisualization(gif) {
            this.gifSrc = `data:image/gif;base64,${gif}`;
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
                console.error('結果のダウンロードに失敗しました:', error);
            });
        },
        showAlert(message, variant) {
            this.alertMessage = message;
            this.alertVariant = variant;
            this.alertVisible = true;
        },
    }
}
</script>

<style>
.table-row {
    cursor: pointer;
}

.custom-modal .modal-dialog {
    max-width: 60%;
}

.custom-modal .modal-body {
    display: flex;
    flex-direction: column;
    height: 80vh;
    padding: 10px;
}

.big-spinner {
    width: 2rem;
    height: 2rem;
    color: #850491;
}
</style>
