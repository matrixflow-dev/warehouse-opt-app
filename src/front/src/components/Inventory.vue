<template>
    <div>
        <h1>在庫情報</h1>
        <p>在庫情報を表示します。</p>
        <b-table :items="stocks" :fields="fields"></b-table>
        <b-pagination v-model="currentPage" :total-rows="totalStocks" :per-page="perPage" @change="fetchStocks"
            aria-controls="inventory-table"></b-pagination>
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
                { key: 'created_at', label: '作成日時' },
                { key: 'description', label: '説明' },
            ],
            currentPage: 1,
            perPage: 10,
        };
    },
    mounted() {
        this.fetchStocks();
    },
    methods: {
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
        }
    }
}
</script>
