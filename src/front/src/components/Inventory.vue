<template>
    <div>
        <h1>在庫情報</h1>
        <p>在庫情報を管理します。</p>

        <!-- 新規追加アイコン -->
        <b-button variant="success" @click="toggleForm" class="mb-3" v-b-tooltip.hover title="新規追加">
            <b-icon icon="plus-circle"></b-icon>
        </b-button>

        <!-- アラートメッセージ -->
        <b-alert :show="alertVisible" :variant="alertVariant" dismissible @dismissed="alertVisible = false"
            class="mb-3">
            {{ alertMessage }}
        </b-alert>

        <!-- フォーム表示（カード形式） -->
        <b-card v-if="showForm" class="mb-3">
            <b-form @submit.prevent="addStock">
                <b-form-group label="名前">
                    <b-form-input v-model="name" placeholder="名前を入力"></b-form-input>
                </b-form-group>
                <b-form-group label="説明">
                    <b-form-input v-model="description" placeholder="説明を入力"></b-form-input>
                </b-form-group>
                <b-form-group label="JSONファイル">
                    <b-form-file v-model="jsonFile" accept=".json" placeholder="stock.jsonファイルを選択..."
                        browse-text="ファイルを選択"></b-form-file>
                </b-form-group>
                <b-button type="submit" variant="primary" class="mt-2">追加</b-button>
            </b-form>
        </b-card>

        <!-- テーブル -->
        <b-table :items="stocks" :fields="fields" @row-clicked="onRowClicked">
            <template #cell(id)="data">
                <span class="table-row" v-b-tooltip.hover title="クリックすると詳細表示">{{ data.item.id }}</span>
            </template>
            <template #cell(name)="data">
                <span class="table-row" v-b-tooltip.hover title="クリックすると詳細表示">{{ data.item.name}}</span>
            </template>
            <template #cell(description)="data">
                <span class="table-row" v-b-tooltip.hover title="クリックすると詳細表示">{{ data.item.description }}</span>
            </template>
            <template #cell(created_at)="data">
                <span class="table-row" v-b-tooltip.hover title="クリックすると詳細表示">{{ data.item.created_at }}</span>
            </template>
        </b-table>

        <b-pagination v-model="currentPage" :total-rows="totalStocks" :per-page="perPage" @change="fetchStocks"
            aria-controls="inventory-table"></b-pagination>

        <!-- 詳細モーダル -->
        <b-modal v-if="selectedStock" @hide="selectedStock = null" title="在庫詳細" :visible="showModal"
            modal-class="custom-modal">
            <p><strong>ID:</strong> {{ selectedStock.id }}</p>
            <p><strong>名前:</strong> {{ selectedStock.name}}</p>
            <p><strong>説明:</strong> {{ selectedStock.description }}</p>
            <p><strong>作成日時:</strong> {{ selectedStock.created_at }}</p>

            <!-- フッター -->
            <template #modal-footer>
                <div class="d-flex justify-content-between w-100">
                    <b-button variant="danger" @click="deleteStock" class="mt-3">削除</b-button>
                    <b-button @click="showModal = false" class="mt-3">閉じる</b-button>
                </div>
            </template>
        </b-modal>
    </div>
</template>

<script>
import axios from 'axios';

export default {
    name: 'Inventory',
    data() {
        return {
            stocks: [],
            totalStocks: 0,
            fields: [
                { key: 'id', label: 'ID' },
                { key: 'name', label: '名前' },
                { key: 'description', label: '説明' },
                { key: 'created_at', label: '作成日時' },
            ],
            currentPage: 1,
            perPage: 10,
            name: '',
            description: '', // 説明のデータを格納
            jsonFile: null, // JSONファイルを格納
            showForm: false, // フォームの表示/非表示を制御
            alertVisible: false, // アラートの表示/非表示を制御
            alertMessage: '', // アラートメッセージを格納
            alertVariant: 'success', // アラートのバリアントを格納
            selectedStock: null, // 選択された在庫詳細データを格納
            showModal: false, // モーダルの表示/非表示を制御
        };
    },
    mounted() {
        this.fetchStocks();
    },
    methods: {
        toggleForm() {
            this.showForm = !this.showForm;
        },
        fetchStocks() {
            const offset = (this.currentPage - 1) * this.perPage;
            const limit = this.perPage;

            axios.get('/api/stocks', {
                params: {
                    offset: offset,
                    limit: limit,
                }
            })
                .then(response => {
                    this.stocks = response.data.stocks; // サーバーが在庫リストを `stocks` として返すと仮定
                    this.totalStocks = response.data.total; // サーバーが総在庫数を `total` として返すと仮定
                })
                .catch(error => {
                    console.error('在庫情報の取得に失敗しました:', error);
                });
        },
        addStock() {
            if (!this.jsonFile) {
                this.showAlert('JSONファイルを選択してください', 'danger');
                return;
            }

            const formData = new FormData();
            formData.append('name', this.name);
            formData.append('description', this.description);
            formData.append('file', this.jsonFile);

            axios.post('/api/stocks', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data'
                }
            })
                .then(() => {
                    this.showAlert('在庫が正常に追加されました。', 'success');
                    this.fetchStocks();
                    this.resetForm();
                })
                .catch(error => {
                    console.error('在庫の追加に失敗しました:', error);
                    this.showAlert('在庫の追加に失敗しました。', 'danger');
                });
        },
        resetForm() {
            this.name = '';
            this.description = '';
            this.jsonFile = null;  // Reset the file input
            this.showForm = false;
        },
        showAlert(message, variant) {
            this.alertMessage = message;
            this.alertVariant = variant;
            this.alertVisible = true;
        },
        onRowClicked(item) {
            axios.get(`/api/stocks/${item.id}`)
                .then(response => {
                    this.selectedStock = response.data.stock;
                    this.showModal = true;
                })
                .catch(error => {
                    console.error('詳細情報の取得に失敗しました:', error);
                });
        },
        deleteStock() {
            if (!this.selectedStock) return;

            const id = this.selectedStock.id;

            axios.delete(`/api/stocks/${id}`)
                .then(() => {
                    this.showAlert('在庫が削除されました。', 'success');
                    this.fetchStocks();
                    this.selectedStock = null;
                    this.showModal = false;
                })
                .catch(error => {
                    console.error('在庫の削除に失敗しました:', error);
                    this.showAlert('在庫の削除に失敗しました。', 'danger');
                });
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