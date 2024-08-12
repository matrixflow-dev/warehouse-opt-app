<template>
    <div>
        <h1>マップ管理</h1>
        <p>マップ管理の情報を表示します。</p>

        <!-- JSONファイルアップロードエリア -->
        <b-form @submit.prevent="uploadJsonFile">
            <b-form-file v-model="jsonFile" accept=".json" placeholder="JSONファイルを選択..."
                browse-text="ファイルを選択"></b-form-file>
            <b-button type="submit" variant="primary" class="mt-2">アップロード</b-button>
        </b-form>

        <rack-map />

        <b-table :items="mapConfigs" :fields="fields"></b-table>
        <b-pagination v-model="currentPage" :total-rows="totalMapConfigs" :per-page="perPage" @change="fetchMapConfigs"
            aria-controls="map-management-table"></b-pagination>
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
        };
    },
    mounted() {
        this.fetchMapConfigs();
    },
    methods: {
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
                alert("ファイルを選択してください");
                return;
            }

            const formData = new FormData();
            formData.append('file', this.jsonFile);

            axios.post('/api/map-configs/upload', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data'
                }
            })
                .then(response => {
                    console.log(response)
                    alert('ファイルが正常にアップロードされました。');
                    this.fetchMapConfigs(); // アップロード後にテーブルを更新
                })
                .catch(error => {
                    console.error('ファイルのアップロードに失敗しました:', error);
                    alert('ファイルのアップロードに失敗しました。');
                });
        }
    }
}
</script>
