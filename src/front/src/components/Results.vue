<template>
    <div>
        <h1>結果</h1>
        <p>結果を表示します。</p>

        <!-- テーブル -->
        <b-table :items="results" :fields="fields" @row-clicked="onRowClicked">
            <template #cell(id)="data">
                <span class="table-row" v-b-tooltip.hover title="クリックすると詳細表示">{{ data.item.result_id }}</span>
            </template>
            <template #cell(created_at)="data">
                <span class="table-row" v-b-tooltip.hover title="クリックすると詳細表示">{{ data.item.created_at }}</span>
            </template>
            <template #cell(makespan)="data">
                <span class="table-row" v-b-tooltip.hover title="クリックすると詳細表示">{{ data.item.makespan }}</span>
            </template>
            <template #cell(picker_group)="data">
                <span class="table-row" v-b-tooltip.hover title="クリックすると詳細表示">{{ data.item.picker_group }}</span>
            </template>
            <template #cell(map_info)="data">
                <span class="table-row" v-b-tooltip.hover title="クリックすると詳細表示">{{ data.item.map_info }}</span>
            </template>
            <template #cell(stock_info)="data">
                <span class="table-row" v-b-tooltip.hover title="クリックすると詳細表示">{{ data.item.stock_info }}</span>
            </template>
            <template #cell(picking_list)="data">
                <span class="table-row" v-b-tooltip.hover title="クリックすると詳細表示">{{ data.item.picking_list }}</span>
            </template>
        </b-table>

        <b-pagination v-model="currentPage" :total-rows="totalResults" :per-page="perPage" @change="fetchResults"
            aria-controls="results-table"></b-pagination>

        <!-- 詳細モーダル -->
        <b-modal v-if="selectedResult" @hide="selectedResult = null" title="結果詳細" :visible="showModal"
            modal-class="custom-modal">
            <p><strong>ID:</strong> {{ selectedResult.id }}</p>
            <p><strong>作成日時:</strong> {{ selectedResult.created_at }}</p>
            <p><strong>最大時間:</strong> {{ selectedResult.makespan }}</p>
            <p><strong>ピッカーグループ:</strong> {{ selectedResult.picker_group }}</p>
            <p><strong>マップ情報:</strong> {{ selectedResult.map_info }}</p>
            <p><strong>在庫情報:</strong> {{ selectedResult.stock_info }}</p>
            <p><strong>ピッキングリスト:</strong> {{ selectedResult.picking_list }}</p>

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

export default {
    name: 'Results',
    data() {
        return {
            results: [],
            totalResults: 0,
            fields: [
                { key: 'id', label: 'ID' },
                { key: 'created_at', label: '作成日時' },
                { key: 'makespan', label: '最大時間' },
                { key: 'picker_group', label: 'ピッカーグループ' },
                { key: 'map_info', label: 'マップ情報' },
                { key: 'stock_info', label: '在庫情報' },
                { key: 'picking_list', label: 'ピッキングリスト' },
            ],
            currentPage: 1,
            perPage: 10,
            selectedResult: null, // 選択された結果の詳細データを格納
            showModal: false, // モーダルの表示/非表示を制御
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
                params: {
                    offset: offset,
                    limit: limit,
                }
            })
                .then(response => {
                    this.results = response.data.results; // サーバーが結果リストを `results` として返すと仮定
                    this.totalResults = response.data.total; // サーバーが総結果数を `total` として返すと仮定
                })
                .catch(error => {
                    console.error('結果情報の取得に失敗しました:', error);
                });
        },
        onRowClicked(item) {
            axios.get(`/api/results/${item.id}`)
                .then(response => {
                    this.selectedResult = response.data.result;
                    this.showModal = true;
                })
                .catch(error => {
                    console.error('詳細情報の取得に失敗しました:', error);
                });
        },
        deleteResult() {
            if (!this.selectedResult) return;

            const id = this.selectedResult.id;

            axios.delete(`/api/results/${id}`)
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
</style>