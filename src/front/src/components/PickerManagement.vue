<template>
    <div>
        <h1>ピッカー管理</h1>
        <p>ピッカーグループを管理します。</p>

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
            <b-form @submit.prevent="addPicker">
                <b-form-group label="名前">
                    <b-form-input v-model="name" placeholder="名前を入力"></b-form-input>
                </b-form-group>
                <b-form-group label="説明">
                    <b-form-input v-model="description" placeholder="説明を入力"></b-form-input>
                </b-form-group>
                <b-form-group label="JSONファイル">
                    <b-form-file v-model="jsonFile" accept=".json" placeholder="picker.jsonファイルを選択..."
                        browse-text="ファイルを選択"></b-form-file>
                </b-form-group>
                <b-button type="submit" variant="primary" class="mt-2">追加</b-button>
            </b-form>
        </b-card>

        <!-- テーブル -->
        <b-table :items="pickers" :fields="fields" @row-clicked="onRowClicked">
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

        <b-pagination v-model="currentPage" :total-rows="totalPickers" :per-page="perPage" @change="fetchPickers"
            aria-controls="picker-table"></b-pagination>

        <!-- 詳細モーダル -->
        <b-modal v-if="selectedPicker" @hide="selectedPicker = null" title="ピッカー詳細" :visible="showModal"
            modal-class="custom-modal">
            <p><strong>ID:</strong> {{ selectedPicker.id }}</p>
            <p><strong>名前:</strong> {{ selectedPicker.name }}</p>
            <p><strong>説明:</strong> {{ selectedPicker.description }}</p>
            <p><strong>作成日時:</strong> {{ selectedPicker.created_at }}</p>

            <!-- フッター -->
            <template #modal-footer>
                <div class="d-flex justify-content-between w-100">
                    <b-button variant="danger" @click="deletePicker" class="mt-3">削除</b-button>
                    <b-button @click="showModal = false" class="mt-3">閉じる</b-button>
                </div>
            </template>
        </b-modal>
    </div>
</template>

<script>
import axios from 'axios';

export default {
    name: 'PickerManagement',
    data() {
        return {
            pickers: [],
            totalPickers: 0,
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
            selectedPicker: null, // 選択されたピッカー詳細データを格納
            showModal: false, // モーダルの表示/非表示を制御
        };
    },
    mounted() {
        this.fetchPickers();
    },
    methods: {
        toggleForm() {
            this.showForm = !this.showForm;
        },
        fetchPickers() {
            const offset = (this.currentPage - 1) * this.perPage;
            const limit = this.perPage;

            axios.get('/api/agents', {
                params: {
                    offset: offset,
                    limit: limit,
                }
            })
                .then(response => {
                    this.pickers = response.data.agents; // サーバーがエージェントリストを `agents` として返すと仮定
                    this.totalPickers = response.data.total; // サーバーが総エージェント数を `total` として返すと仮定
                })
                .catch(error => {
                    console.error('エージェント情報の取得に失敗しました:', error);
                });
        },
        addPicker() {
            if (!this.jsonFile) {
                this.showAlert('JSONファイルを選択してください', 'danger');
                return;
            }

            const formData = new FormData();
            formData.append('name', this.name);
            formData.append('description', this.description);
            formData.append('file', this.jsonFile);

            axios.post('/api/agents', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data'
                }
            })
                .then(() => {
                    this.showAlert('エージェントが正常に追加されました。', 'success');
                    this.fetchPickers();
                    this.resetForm();
                })
                .catch(error => {
                    console.error('エージェントの追加に失敗しました:', error);
                    this.showAlert('エージェントの追加に失敗しました。', 'danger');
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
            axios.get(`/api/agents/${item.id}`)
                .then(response => {
                    this.selectedPicker = response.data.agent;
                    this.showModal = true;
                })
                .catch(error => {
                    console.error('詳細情報の取得に失敗しました:', error);
                });
        },
        deletePicker() {
            if (!this.selectedPicker) return;

            const id = this.selectedPicker.id;

            axios.delete(`/api/agents/${id}`)
                .then(() => {
                    this.showAlert('エージェントが削除されました。', 'success');
                    this.fetchPickers();
                    this.selectedPicker = null;
                    this.showModal = false;
                })
                .catch(error => {
                    console.error('エージェントの削除に失敗しました:', error);
                    this.showAlert('エージェントの削除に失敗しました。', 'danger');
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