<template>
    <b-container class="mt-3">
        <b-card title="API管理" class="mb-3">
            <b-card-text>
                APIを管理します。
            </b-card-text>
            <b-list-group>
                <b-list-group-item>
                    <strong>Endpoint:</strong>
                    <b-badge variant="secondary" class="rounded-pill bg-light text-dark">{{ apiData.endpoint
                        }}</b-badge>
                    <b-button variant="outline-secondary" class="ml-2" @click="copyToClipboard(apiData.endpoint)">
                        📋
                    </b-button>
                </b-list-group-item>
                <b-list-group-item>
                    <strong>Secret Key:</strong>
                    <b-badge variant="secondary" class="rounded-pill bg-light text-dark">{{ apiData.secret_key
                        }}</b-badge>
                    <b-button variant="outline-secondary" class="ml-2" @click="copyToClipboard(apiData.secret_key)">
                        📋
                    </b-button>
                </b-list-group-item>
            </b-list-group>
        </b-card>
        <b-alert v-model="showAlert" variant="success" dismissible>
            {{ alertMessage }}
        </b-alert>
        <div class="iframe-container mt-3">
            <iframe :src="iframeSrc" frameborder="0" class="iframe-content"></iframe>
        </div>
    </b-container>
</template>

<script>
import axios from 'axios';
import { BContainer, BCard, BCardText, BListGroup, BListGroupItem, BButton, BAlert, BBadge } from 'bootstrap-vue';

export default {
    name: 'APIManagement',
    components: {
        BContainer,
        BCard,
        BCardText,
        BListGroup,
        BListGroupItem,
        BButton,
        BAlert,
        BBadge
    },
    data() {
        return {
            apiData: null,
            showAlert: false,
            alertMessage: ''
        };
    },
    computed: {
        iframeSrc() {
            // Construct the URL dynamically based on the current location
            return `${window.location.protocol}//${window.location.host}/docs`;
        }
    },
    mounted() {
        this.fetchApiData();
    },
    methods: {
        async fetchApiData() {
            try {
                const response = await axios.get('/api/api/');
                this.apiData = response.data;
            } catch (error) {
                console.error('Error fetching API data:', error);
            }
        },
        copyToClipboard(text) {
            navigator.clipboard.writeText(text)
                .then(() => {
                    this.alertMessage = 'コピーしました';
                    this.showAlert = true;
                })
                .catch(err => {
                    console.error('Failed to copy text:', err);
                    this.alertMessage = 'Failed to copy text.';
                    this.showAlert = true;
                });
        }
    }
}
</script>

<style scoped>
.b-card {
    border-color: #e9ecef;
}

.badge {
    font-size: 20px;
    background-color: #f8f9fa;
    /* Light gray background */
    color: #343a40;
    /* Dark text for contrast */
    border-radius: 1.25rem;
    /* Rounded corners */
    padding: 0.5rem 1rem;
    /* Padding */
}

.iframe-container {
    position: relative;
    overflow: hidden;
    padding-top: 56.25%;
    /* 16:9 Aspect Ratio */
    height: 0;
    margin-top: 1rem;
}

.iframe-content {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
}
</style>
