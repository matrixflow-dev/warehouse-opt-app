<template>
    <div>
        <h1>マップ管理</h1>
        <p>マップ管理の情報を表示します。</p>

        <!-- 新規追加アイコン -->
        <b-button variant="success" @click="toggleForm" class="mb-3" v-b-tooltip.hover title="新規追加">
            <b-icon icon="plus-circle"></b-icon>
        </b-button>

        <!-- アラートメッセージ -->
        <b-alert :show="alertVisible" :variant="alertVariant" dismissible @dismissed="alertVisible = false"
            class="mb-3">
            {{ alertMessage }}
        </b-alert>

        <!-- JSONファイルアップロードエリア（カード表示） -->
        <b-card v-if="showForm" class="mb-3">
            <b-form @submit.prevent="uploadJsonFile">
                <b-form-group label="名前">
                    <b-form-input v-model="name" placeholder="名前を入力"></b-form-input>
                </b-form-group>
                <b-form-group label="説明">
                    <b-form-input v-model="description" placeholder="説明を入力"></b-form-input>
                </b-form-group>
                <b-form-file v-model="jsonFile" accept=".json" placeholder="config.jsonファイルを選択..."
                    browse-text="ファイルを選択"></b-form-file>
                <b-button type="submit" variant="primary" class="mt-2">アップロード</b-button>
            </b-form>
        </b-card>

        <rack-map />

        <!-- テーブル -->
        <b-table :items="mapConfigs" :fields="fields" @row-clicked="onRowClicked">
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

        <b-pagination v-model="currentPage" :total-rows="totalMapConfigs" :per-page="perPage" @change="fetchMapConfigs"
            aria-controls="map-management-table"></b-pagination>

        <!-- 詳細モーダル -->
        <b-modal v-if="selectedMapConfig" @hide="selectedMapConfig = null" title="マップ設定詳細" :visible="showModal">
            <p><strong>ID:</strong> {{ selectedMapConfig.id }}</p>
            <p><strong>名前:</strong> {{ selectedMapConfig.name }}</p>
            <p><strong>説明:</strong> {{ selectedMapConfig.description }}</p>
            <p><strong>作成日時:</strong> {{ selectedMapConfig.created_at }}</p>
        </b-modal>
    </div>
</template>

<script>
import axios from 'axios';

export default {
    name: 'MapManagement',
    data() {
        return {
            mapConfigs: [],
            totalMapConfigs: 0,
            fields: [
                { key: 'id', label: 'ID' },
                { key: 'name', label: '名前' },
                { key: 'description', label: '説明' },
                { key: 'created_at', label: '作成日時' },
            ],
            currentPage: 1,
            perPage: 10,
            jsonFile: null,  // JSONファイルを格納
            name: '', // 名前のデータを格納
            description: '', // 説明のデータを格納
            showForm: false, // フォームの表示/非表示を制御
            alertVisible: false, // アラートの表示/非表示を制御
            alertMessage: '', // アラートメッセージを格納
            alertVariant: 'success', // アラートのバリアントを格納
            selectedMapConfig: null, // 選択されたマップ設定の詳細データを格納
            showModal: false, // モーダルの表示/非表示を制御
        };
    },
    mounted() {
        this.fetchMapConfigs();
    },
    methods: {
        toggleForm() {
            this.showForm = !this.showForm;
        },
        fetchMapConfigs() {
            const offset = (this.currentPage - 1) * this.perPage;
            const limit = this.perPage;

            axios.get('/api/map-configs', {
                params: {
                    offset: offset,
                    limit: limit,
                }
            })
                .then(response => {
                    this.mapConfigs = response.data.mapConfigs; // サーバーがマップ設定リストを `mapConfigs` として返すと仮定
                    this.totalMapConfigs = response.data.total; // サーバーが総マップ設定数を `total` として返すと仮定
                })
                .catch(error => {
                    console.error('マップ管理情報の取得に失敗しました:', error);
                });
        },
        uploadJsonFile() {
            if (!this.jsonFile) {
                this.showAlert('ファイルを選択してください', 'danger');
                return;
            }

            const formData = new FormData();
            formData.append('file', this.jsonFile);
            formData.append('name', this.name);
            formData.append('description', this.description);

            axios.post('/api/map-configs/upload', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data'
                }
            })
                .then(response => {
                    console.log(response)
                    this.showAlert('ファイルが正常にアップロードされました。', 'success');
                    this.fetchMapConfigs(); // アップロード後にテーブルを更新
                    this.resetForm(); // フォームをリセットして非表示にする
                })
                .catch(error => {
                    console.error('ファイルのアップロードに失敗しました:', error);
                    this.showAlert('ファイルのアップロードに失敗しました。', 'danger');
                });
        },
        resetForm() {
            this.jsonFile = null;
            this.name = '';
            this.description = '';
            this.showForm = false;
        },
        showAlert(message, variant) {
            this.alertMessage = message;
            this.alertVariant = variant;
            this.alertVisible = true;
        },
        onRowClicked(item) {
            axios.get(`/api/map-configs/${item.id}`)
                .then(response => {
                    this.selectedMapConfig = response.data;
                    this.showModal = true;
                })
                .catch(error => {
                    console.error('詳細情報の取得に失敗しました:', error);
                });
        },
    }
}
</script>

<style>
.table-row {
    cursor: pointer;
}
</style>