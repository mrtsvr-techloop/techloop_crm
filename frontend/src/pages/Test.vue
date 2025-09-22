<template>
  <div class="flex flex-col h-full overflow-hidden">
    <LayoutHeader>
      <template #left-header>
        <ViewBreadcrumbs routeName="Test" />
      </template>
      <template #right-header>
        <Button
          :label="__('Refresh')"
          :iconLeft="LucideRefreshCcw"
          @click="refreshData"
        />
        <Button
          variant="solid"
          :label="__('Add Test Item')"
          :iconLeft="LucidePlus"
          @click="showAddModal = true"
        />
      </template>
    </LayoutHeader>

    <div class="p-5 flex-1 overflow-y-auto">
      <div class="mb-6">
        <h1 class="text-2xl font-semibold text-ink-gray-8 mb-2">
          {{ __('Test Page') }}
        </h1>
        <p class="text-ink-gray-6">
          {{ __('This is a test page to demonstrate how to add custom pages to the CRM.') }}
        </p>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
        <div class="bg-surface-gray-1 rounded-lg p-4">
          <div class="flex items-center gap-3 mb-2">
            <div class="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
              <LucideUsers class="w-4 h-4 text-blue-600" />
            </div>
            <h3 class="font-medium text-ink-gray-8">{{ __('Total Items') }}</h3>
          </div>
          <p class="text-2xl font-bold text-ink-gray-8">{{ testData.length }}</p>
        </div>

        <div class="bg-surface-gray-1 rounded-lg p-4">
          <div class="flex items-center gap-3 mb-2">
            <div class="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
              <LucideCheckCircle class="w-4 h-4 text-green-600" />
            </div>
            <h3 class="font-medium text-ink-gray-8">{{ __('Completed') }}</h3>
          </div>
          <p class="text-2xl font-bold text-ink-gray-8">{{ completedCount }}</p>
        </div>

        <div class="bg-surface-gray-1 rounded-lg p-4">
          <div class="flex items-center gap-3 mb-2">
            <div class="w-8 h-8 bg-orange-100 rounded-full flex items-center justify-center">
              <LucideClock class="w-4 h-4 text-orange-600" />
            </div>
            <h3 class="font-medium text-ink-gray-8">{{ __('Pending') }}</h3>
          </div>
          <p class="text-2xl font-bold text-ink-gray-8">{{ pendingCount }}</p>
        </div>
      </div>

      <div class="bg-white rounded-lg border border-gray-200">
        <div class="p-4 border-b border-gray-200">
          <h2 class="text-lg font-medium text-ink-gray-8">{{ __('Test Items') }}</h2>
        </div>
        <div class="p-4">
          <div v-if="testData.length === 0" class="text-center py-8 text-ink-gray-6">
            <LucideFileText class="w-12 h-12 mx-auto mb-3 text-ink-gray-4" />
            <p>{{ __('No test items found. Click "Add Test Item" to get started.') }}</p>
          </div>
          <div v-else class="space-y-3">
            <div
              v-for="item in testData"
              :key="item.id"
              class="flex items-center justify-between p-3 bg-surface-gray-1 rounded-lg"
            >
              <div class="flex items-center gap-3">
                <div class="w-2 h-2 rounded-full" :class="item.status === 'completed' ? 'bg-green-500' : 'bg-orange-500'"></div>
                <div>
                  <p class="font-medium text-ink-gray-8">{{ item.title }}</p>
                  <p class="text-sm text-ink-gray-6">{{ item.description }}</p>
                </div>
              </div>
              <div class="flex items-center gap-2">
                <Badge
                  :label="item.status"
                  :variant="item.status === 'completed' ? 'subtle' : 'outline'"
                />
                <Button
                  variant="ghost"
                  size="sm"
                  :iconLeft="LucideTrash2"
                  @click="removeItem(item.id)"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Add Test Item Modal -->
    <Dialog v-model="showAddModal" :options="{ title: __('Add Test Item') }">
      <template #body-content>
        <div class="space-y-4">
          <Input
            v-model="newItem.title"
            :label="__('Title')"
            :placeholder="__('Enter item title')"
          />
          <Textarea
            v-model="newItem.description"
            :label="__('Description')"
            :placeholder="__('Enter item description')"
          />
          <Dropdown
            v-model="newItem.status"
            :options="statusOptions"
            :label="__('Status')"
          />
        </div>
      </template>
      <template #actions>
        <Button variant="ghost" :label="__('Cancel')" @click="showAddModal = false" />
        <Button
          variant="solid"
          :label="__('Add Item')"
          :disabled="!newItem.title"
          @click="addItem"
        />
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import LucideRefreshCcw from '~icons/lucide/refresh-ccw'
import LucidePlus from '~icons/lucide/plus'
import LucideUsers from '~icons/lucide/users'
import LucideCheckCircle from '~icons/lucide/check-circle'
import LucideClock from '~icons/lucide/clock'
import LucideFileText from '~icons/lucide/file-text'
import LucideTrash2 from '~icons/lucide/trash-2'
import { Button, Dialog, Input, Textarea, Dropdown, Badge } from 'frappe-ui'
import { ref, computed } from 'vue'
import { usePageMeta } from 'frappe-ui'

// Sample data
const testData = ref([
  {
    id: 1,
    title: 'Sample Test Item 1',
    description: 'This is a sample test item for demonstration purposes.',
    status: 'completed'
  },
  {
    id: 2,
    title: 'Sample Test Item 2',
    description: 'Another sample test item to show the functionality.',
    status: 'pending'
  }
])

const showAddModal = ref(false)
const newItem = ref({
  title: '',
  description: '',
  status: 'pending'
})

const statusOptions = [
  { label: __('Pending'), value: 'pending' },
  { label: __('Completed'), value: 'completed' }
]

const completedCount = computed(() => 
  testData.value.filter(item => item.status === 'completed').length
)

const pendingCount = computed(() => 
  testData.value.filter(item => item.status === 'pending').length
)

function refreshData() {
  // Simulate data refresh
  console.log('Refreshing test data...')
}

function addItem() {
  if (!newItem.value.title) return
  
  const item = {
    id: Date.now(),
    title: newItem.value.title,
    description: newItem.value.description,
    status: newItem.value.status
  }
  
  testData.value.push(item)
  
  // Reset form
  newItem.value = {
    title: '',
    description: '',
    status: 'pending'
  }
  
  showAddModal.value = false
}

function removeItem(id) {
  const index = testData.value.findIndex(item => item.id === id)
  if (index > -1) {
    testData.value.splice(index, 1)
  }
}

usePageMeta(() => {
  return { title: __('Test Page') }
})
</script>
