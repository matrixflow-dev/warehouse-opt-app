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

                <!-- グループテーブル -->
                <b-table :items="groups" :fields="groupFields" class="mt-3">
                    <template #cell(agent_id)="data">
                        {{ data.item.agent_id }}
                    </template>
                    <template #cell(amount)="data">
                        <b-form-input type="number" v-model="data.item.amount"></b-form-input>
                    </template>
                    <template #cell(initial_place_row)="data">
                        <b-form-input type="number" v-model="data.item.initial_place_row"></b-form-input>
                    </template>
                    <template #cell(initial_place_col)="data">
                        <b-form-input type="number" v-model="data.item.initial_place_col"></b-form-input>
                    </template>
                    <template #cell(name)="data">
                        <b-form-input v-model="data.item.name"></b-form-input>
                    </template>
                    <template #cell(actions)="data">
                        <b-button variant="danger" @click="removeGroup(data.index)">削除</b-button>
                    </template>
                </b-table>
                <b-row>
                    <b-button @click="addGroup" class="mt-2">グループ追加</b-button>
                </b-row>
                <b-row>
                    <b-button type="submit" variant="primary" class="mt-2">追加</b-button>
                </b-row>
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

            <!-- グループテーブル -->
            <b-table :items="selectedPicker.group" :fields="showGroupFields" class="mt-3">
                <template #cell(agent_id)="data">
                    {{ data.item.agent_id }}
                </template>
                <template #cell(name)="data">
                    {{ data.item.name }}
                </template>
                <template #cell(amount)="data">
                    {{ data.item.amount }}
                </template>
                <template #cell(initial_place_row)="data">
                    {{ data.item.initial_place_row }}
                </template>
                <template #cell(initial_place_col)="data">
                    {{ data.item.initial_place_col }}
                </template>
            </b-table>

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
            groupFields: [
                { key: 'agent_id', label: 'エージェントID' },
                { key: 'name', label: '名前' },
                { key: 'amount', label: '数量' },
                { key: 'initial_place_row', label: '初期行' },
                { key: 'initial_place_col', label: '初期列' },
                { key: 'actions', label: '操作' }
            ],
            showGroupFields: [
                { key: 'agent_id', label: 'エージェントID' },
                { key: 'name', label: '名前' },
                { key: 'amount', label: '数量' },
                { key: 'initial_place_row', label: '初期行' },
                { key: 'initial_place_col', label: '初期列' },
            ],
            currentPage: 1,
            perPage: 10,
            name: '',
            description: '',
            groups: [{ // 初期値として1行を用意
                agent_id: 'agent1',
                amount: 0,
                initial_place_row: 0,
                initial_place_col: 0,
                name: ''
            }],
            showForm: false,
            alertVisible: false,
            alertMessage: '',
            alertVariant: 'success',
            selectedPicker: null,
            showModal: false,
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
                    this.pickers = response.data.agents;
                    this.totalPickers = response.data.total;
                })
                .catch(error => {
                    console.error('ピッカー情報の取得に失敗しました:', error);
                });
        },
        addPicker() {
            const formData = {
                name: this.name,
                description: this.description,
                group: this.groups
            };

            axios.post('/api/agents', formData, {
                headers: {
                    'Content-Type': 'application/json'
                }
            })
                .then(() => {
                    this.showAlert('ピッカー情報が正常に追加されました。', 'success');
                    this.fetchPickers();
                    this.resetForm();
                })
                .catch(error => {
                    console.error('ピッカー情報の追加に失敗しました:', error);
                    this.showAlert('ピッカー情報の追加に失敗しました。', 'danger');
                });
        },
        resetForm() {
            this.name = '';
            this.description = '';
            this.groups = [{ // 初期値として1行を用意
                agent_id: 'agent1',
                amount: 0,
                initial_place_row: 0,
                initial_place_col: 0,
                name: ''
            }];
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
                    this.showAlert('ピッカー情報が削除されました。', 'success');
                    this.fetchPickers();
                    this.selectedPicker = null;
                    this.showModal = false;
                })
                .catch(error => {
                    console.error('ピッカー情報の削除に失敗しました:', error);
                    this.showAlert('ピッカー情報の削除に失敗しました。', 'danger');
                });
        },
        addGroup() {
            const nextAgentId = `agent${this.groups.length + 1}`;
            this.groups.push({
                agent_id: nextAgentId,
                amount: 0,
                initial_place_row: 0,
                initial_place_col: 0,
                name: ''
            });
        },
        removeGroup(index) {
            if (this.groups.length > 1) {
                this.groups.splice(index, 1);
            } else {
                this.showAlert('少なくとも1つのグループが必要です。', 'danger');
            }
        }
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

.custom-modal .b-table {
    margin-top: 20px;
}
</style>