<template>
    <div>
        <b-form-group label="Select Agents:">
            <b-form-select v-model="selectedAgents" multiple>
                <b-form-select-option v-for="agent in agentOptions" :key="agent" :value="agent">
                    {{ agent }}
                </b-form-select-option>
            </b-form-select>
        </b-form-group>

        <b-form-group label="Select Map Config:">
            <b-form-select v-model="selectedMapConfig">
                <b-form-select-option v-for="config in mapConfigOptions" :key="config" :value="config">
                    {{ config }}
                </b-form-select-option>
            </b-form-select>
        </b-form-group>

        <b-form-group label="Select Stock:">
            <b-form-select v-model="selectedStock">
                <b-form-select-option v-for="stock in stockOptions" :key="stock" :value="stock">
                    {{ stock }}
                </b-form-select-option>
            </b-form-select>
        </b-form-group>

        <b-form-group label="Select Picking List:">
            <b-form-select v-model="selectedPickingList">
                <b-form-select-option v-for="list in pickingListOptions" :key="list" :value="list">
                    {{ list }}
                </b-form-select-option>
            </b-form-select>
        </b-form-group>

        <b-button variant="primary" @click="sendRequest">Send Request</b-button>
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
            selectedPickingList: ''
        };
    },
    methods: {
        async fetchOptions() {
            try {
                const [agentsRes, mapConfigsRes, stocksRes, pickingListsRes] = await Promise.all([
                    axios.get('/api/agents'),
                    axios.get('/api/map-configs'),
                    axios.get('/api/stocks'),
                    axios.get('/api/picking-lists')
                ]);

                this.agentOptions = agentsRes.data;
                this.mapConfigOptions = mapConfigsRes.data;
                this.stockOptions = stocksRes.data;
                this.pickingListOptions = pickingListsRes.data;
            } catch (error) {
                console.error('Error fetching options:', error);
            }
        },
        async sendRequest() {
            try {
                const payload = {
                    agent_ids: this.selectedAgents,
                    map_config_id: this.selectedMapConfig,
                    stock_id: this.selectedStock,
                    picking_list_id: this.selectedPickingList
                };

                const response = await axios.post('/api/start', payload);
                console.log('Response:', response.data);
            } catch (error) {
                console.error('Error sending request:', error);
            }
        }
    },
    mounted() {
        this.fetchOptions();
    }
};
</script>