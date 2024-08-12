<template>
    <div>
        <h1>ピッキングリスト管理</h1>
        <p>ピッキングリストを管理します。</p>

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
            <b-form @submit.prevent="addPickingList">
                <b-form-group label="名前">
                    <b-form-input v-model="name" placeholder="名前を入力"></b-form-input>
                </b-form-group>
                <b-form-group label="説明">
                    <b-form-input v-model="description" placeholder="説明を入力"></b-form-input>
                </b-form-group>
                <b-form-group label="JSONファイル">
                    <b-form-file v-model="csvFile" accept=".csv" placeholder="list.csvファイルを選択..."
                        browse-text="ファイルを選択"></b-form-file>
                </b-form-group>
                <b-button type="submit" variant="primary" class="mt-2">追加</b-button>
            </b-form>
        </b-card>

        <!-- テーブル -->
        <b-table :items="pickingLists" :fields="fields" @row-clicked="onRowClicked">
            <template #cell(id)="data">
                <span class="table-row" v-b-tooltip.hover title="クリックすると詳細表示">{{ data.item.id }}</span>
            </template>
            <template #cell(name)="data">
                <span class="table-row" v-b-tooltip.hover title="クリックすると詳細表示">{{ data.item.name }}</span>
            </template>
            <template #cell(description)="data">
                <span class="table-row" v-b-tooltip.hover title="クリックすると詳細表示">{{ data.item.description }}</span>
            </template>
            <template #cell(created_at)="data">
                <span class="table-row" v-b-tooltip.hover title="クリックすると詳細表示">{{ data.item.created_at }}</span>
            </template>
        </b-table>

        <b-pagination v-model="currentPage" :total-rows="totalPickingLists" :per-page="perPage"
            @change="fetchPickingLists" aria-controls="picking-list-table"></b-pagination>

        <!-- 詳細モーダル -->
        <b-modal v-if="selectedPickingList" @hide="selectedPickingList = null" title="ピッキングリスト詳細" :visible="showModal"
            modal-class="custom-modal">
            <p><strong>ID:</strong> {{ selectedPickingList.id }}</p>
            <p><strong>名前:</strong> {{ selectedPickingList.name }}</p>
            <p><strong>説明:</strong> {{ selectedPickingList.description }}</p>
            <p><strong>作成日時:</strong> {{ selectedPickingList.created_at }}</p>

            <!-- フッター -->
            <template #modal-footer>
                <div class="d-flex justify-content-between w-100">
                    <b-button variant="danger" @click="deletePickingList" class="mt-3">削除</b-button>
                    <b-button @click="showModal = false" class="mt-3">閉じる</b-button>
                </div>
            </template>
        </b-modal>
    </div>
</template>

<script>
import axios from 'axios';

export default {
    name: 'PickingList',
    data() {
        return {
            pickingLists: [],
            totalPickingLists: 0,
            fields: [
                { key: 'id', label: 'ID' },
                { key: 'name', label: '名前' },
                { key: 'description', label: '説明' },
                { key: 'created_at', label: '作成日時' },
            ],
            currentPage: 1,
            perPage: 10,
            name: '',
            description: '',
            csvFile: null,
            showForm: false,
            alertVisible: false,
            alertMessage: '',
            alertVariant: 'success',
            selectedPickingList: null,
            showModal: false,
        };
    },
    mounted() {
        this.fetchPickingLists();
    },
    methods: {
        toggleForm() {
            this.showForm = !this.showForm;
        },
        fetchPickingLists() {
            const offset = (this.currentPage - 1) * this.perPage;
            const limit = this.perPage;

            axios.get('/api/picking-lists', {
                params: {
                    offset: offset,
                    limit: limit,
                }
            })
                .then(response => {
                    this.pickingLists = response.data.pickingLists; // サーバーがピッキングリストを `pickingLists` として返すと仮定
                    this.totalPickingLists = response.data.total; // サーバーが総ピッキングリスト数を `total` として返すと仮定
                })
                .catch(error => {
                    console.error('ピッキングリストの取得に失敗しました:', error);
                });
        },
        addPickingList() {
            if (!this.csvFile) {
                this.showAlert('CSVファイルを選択してください', 'danger');
                return;
            }

            const formData = new FormData();
            formData.append('name', this.name);
            formData.append('description', this.description);
            formData.append('file', this.csvFile);

            axios.post('/api/picking-lists', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data'
                }
            })
                .then(() => {
                    this.showAlert('ピッキングリストが正常に追加されました。', 'success');
                    this.fetchPickingLists();
                    this.resetForm();
                })
                .catch(error => {
                    console.error('ピッキングリストの追加に失敗しました:', error);
                    this.showAlert('ピッキングリストの追加に失敗しました。', 'danger');
                });
        },
        resetForm() {
            this.name = '';
            this.description = '';
            this.csvFile = null;
            this.showForm = false;
        },
        showAlert(message, variant) {
            this.alertMessage = message;
            this.alertVariant = variant;
            this.alertVisible = true;
        },
        onRowClicked(item) {
            axios.get(`/api/picking-lists/${item.id}`)
                .then(response => {
                    this.selectedPickingList = response.data.pickingList;
                    this.showModal = true;
                })
                .catch(error => {
                    console.error('詳細情報の取得に失敗しました:', error);
                });
        },
        deletePickingList() {
            if (!this.selectedPickingList) return;

            const id = this.selectedPickingList.id;

            axios.delete(`/api/picking-lists/${id}`)
                .then(() => {
                    this.showAlert('ピッキングリストが削除されました。', 'success');
                    this.fetchPickingLists();
                    this.selectedPickingList = null;
                    this.showModal = false;
                })
                .catch(error => {
                    console.error('ピッキングリストの削除に失敗しました:', error);
                    this.showAlert('ピッキングリストの削除に失敗しました。', 'danger');
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
