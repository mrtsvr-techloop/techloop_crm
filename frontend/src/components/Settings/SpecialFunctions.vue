<template>
  <div class="flex flex-col h-full gap-6 p-6">
    <div class="flex flex-col gap-2">
      <h2 class="text-xl font-semibold text-ink-gray-8">
        {{ __('Special Functions') }}
      </h2>
      <p class="text-sm text-ink-gray-6">
        {{ __('Administrative functions for system management') }}
      </p>
    </div>

    <div class="flex flex-col gap-4">
      <!-- Pulizia Database -->
      <div class="rounded-lg border border-outline-gray-2 bg-surface-white p-6">
        <div class="flex flex-col gap-4">
          <div class="flex items-start justify-between">
            <div class="flex flex-col gap-2">
              <h3 class="text-lg font-semibold text-ink-gray-8">
                {{ __('Clean Database') }}
              </h3>
              <p class="text-sm text-ink-gray-6">
                {{ __('Eliminates all operational data from the CRM:') }}
              </p>
              <ul class="list-disc list-inside text-sm text-ink-gray-6 space-y-1 mt-2">
                <li>{{ __('Deals and Leads') }}</li>
                <li>{{ __('Contacts and Organizations') }}</li>
                <li>{{ __('Products and Tags') }}</li>
                <li>{{ __('Notes and Call Logs') }}</li>
                <li>{{ __('Tasks') }}</li>
              </ul>
              <p class="text-xs text-ink-gray-5 mt-2">
                {{ __('Note: Status, Settings, Users and Permissions are preserved') }}
              </p>
            </div>
          </div>
          <div class="flex items-center gap-3">
            <Button
              variant="danger"
              :loading="cleanDatabase.loading"
              :iconLeft="TrashIcon"
              @click="handleCleanDatabase"
            >
              {{ __('Clean Database') }}
            </Button>
            <Badge
              v-if="cleanResult"
              :variant="cleanResult.success ? 'subtle' : 'subtle'"
              :theme="cleanResult.success ? 'green' : 'red'"
              :label="cleanResult.message"
            />
          </div>
        </div>
      </div>

      <!-- Aggiungi Prodotti -->
      <div class="rounded-lg border border-outline-gray-2 bg-surface-white p-6">
        <div class="flex flex-col gap-4">
          <div class="flex items-start justify-between">
            <div class="flex flex-col gap-2">
              <h3 class="text-lg font-semibold text-ink-gray-8">
                {{ __('Add Default Products') }}
              </h3>
              <p class="text-sm text-ink-gray-6">
                {{ __('Adds default products and tags to the CRM system') }}
              </p>
            </div>
          </div>
          <div class="flex items-center gap-3">
            <Button
              variant="solid"
              :loading="addProducts.loading"
              :iconLeft="PackageIcon"
              @click="handleAddProducts"
            >
              {{ __('Add Products') }}
            </Button>
            <Badge
              v-if="productsResult"
              :variant="productsResult.success ? 'subtle' : 'subtle'"
              :theme="productsResult.success ? 'green' : 'red'"
              :label="productsResult.message"
            />
          </div>
        </div>
      </div>

      <!-- Reset Viste Default -->
      <div class="rounded-lg border border-outline-gray-2 bg-surface-white p-6">
        <div class="flex flex-col gap-4">
          <div class="flex items-start justify-between">
            <div class="flex flex-col gap-2">
              <h3 class="text-lg font-semibold text-ink-gray-8">
                {{ __('Reset Default Views') }}
              </h3>
              <p class="text-sm text-ink-gray-6">
                {{ __('Resets all default views (List and Kanban) for:') }}
              </p>
              <ul class="list-disc list-inside text-sm text-ink-gray-6 space-y-1 mt-2">
                <li>{{ __('CRM Lead (List and Kanban)') }}</li>
                <li>{{ __('CRM Deal (List and Kanban)') }}</li>
                <li>{{ __('Contact (List)') }}</li>
              </ul>
              <p class="text-xs text-ink-gray-5 mt-2">
                {{ __('This will sync columns from database, including all custom statuses for Kanban views') }}
              </p>
            </div>
          </div>
          <div class="flex items-center gap-3">
            <Button
              variant="solid"
              :loading="resetViews.loading"
              :iconLeft="RefreshCwIcon"
              @click="handleResetViews"
            >
              {{ __('Reset Views') }}
            </Button>
            <Badge
              v-if="viewsResult"
              :variant="viewsResult.success ? 'subtle' : 'subtle'"
              :theme="viewsResult.success ? 'green' : 'red'"
              :label="viewsResult.message"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- Risultati Dettagliati -->
    <div v-if="cleanResult && cleanResult.summary" class="rounded-lg border border-outline-gray-2 bg-surface-gray-1 p-4">
      <h4 class="text-sm font-semibold text-ink-gray-8 mb-3">
        {{ __('Cleanup Statistics') }}
      </h4>
      <div class="grid grid-cols-2 md:grid-cols-5 gap-4">
        <div class="flex flex-col gap-1">
          <span class="text-xs text-ink-gray-5">{{ __('Deals') }}</span>
          <span class="text-lg font-semibold text-ink-gray-8">{{ cleanResult.summary.deals || 0 }}</span>
        </div>
        <div class="flex flex-col gap-1">
          <span class="text-xs text-ink-gray-5">{{ __('Leads') }}</span>
          <span class="text-lg font-semibold text-ink-gray-8">{{ cleanResult.summary.leads || 0 }}</span>
        </div>
        <div class="flex flex-col gap-1">
          <span class="text-xs text-ink-gray-5">{{ __('Contacts') }}</span>
          <span class="text-lg font-semibold text-ink-gray-8">{{ cleanResult.summary.contacts || 0 }}</span>
        </div>
        <div class="flex flex-col gap-1">
          <span class="text-xs text-ink-gray-5">{{ __('Organizations') }}</span>
          <span class="text-lg font-semibold text-ink-gray-8">{{ cleanResult.summary.organizations || 0 }}</span>
        </div>
        <div class="flex flex-col gap-1">
          <span class="text-xs text-ink-gray-5">{{ __('Products') }}</span>
          <span class="text-lg font-semibold text-ink-gray-8">{{ cleanResult.summary.products || 0 }}</span>
        </div>
      </div>
    </div>

    <div v-if="productsResult && productsResult.summary" class="rounded-lg border border-outline-gray-2 bg-surface-gray-1 p-4">
      <h4 class="text-sm font-semibold text-ink-gray-8 mb-3">
        {{ __('Products Added') }}
      </h4>
      <div class="flex gap-6">
        <div class="flex flex-col gap-1">
          <span class="text-xs text-ink-gray-5">{{ __('Products Created') }}</span>
          <span class="text-lg font-semibold text-ink-gray-8">{{ productsResult.total_products || 0 }}</span>
        </div>
        <div class="flex flex-col gap-1">
          <span class="text-xs text-ink-gray-5">{{ __('Tags Created') }}</span>
          <span class="text-lg font-semibold text-ink-gray-8">{{ productsResult.created_tags?.length || 0 }}</span>
        </div>
      </div>
    </div>

    <div v-if="viewsResult && viewsResult.summary" class="rounded-lg border border-outline-gray-2 bg-surface-gray-1 p-4">
      <h4 class="text-sm font-semibold text-ink-gray-8 mb-3">
        {{ __('Views Reset') }}
      </h4>
      <div class="grid grid-cols-2 md:grid-cols-3 gap-4">
        <div class="flex flex-col gap-1">
          <span class="text-xs text-ink-gray-5">{{ __('Lead List') }}</span>
          <span class="text-lg font-semibold" :class="viewsResult.summary.leads?.list ? 'text-green-600' : 'text-red-600'">
            {{ viewsResult.summary.leads?.list ? __('Success') : __('Failed') }}
          </span>
        </div>
        <div class="flex flex-col gap-1">
          <span class="text-xs text-ink-gray-5">{{ __('Lead Kanban') }}</span>
          <span class="text-lg font-semibold" :class="viewsResult.summary.leads?.kanban ? 'text-green-600' : 'text-red-600'">
            {{ viewsResult.summary.leads?.kanban ? __('Success') : __('Failed') }}
          </span>
        </div>
        <div class="flex flex-col gap-1">
          <span class="text-xs text-ink-gray-5">{{ __('Deal List') }}</span>
          <span class="text-lg font-semibold" :class="viewsResult.summary.deals?.list ? 'text-green-600' : 'text-red-600'">
            {{ viewsResult.summary.deals?.list ? __('Success') : __('Failed') }}
          </span>
        </div>
        <div class="flex flex-col gap-1">
          <span class="text-xs text-ink-gray-5">{{ __('Deal Kanban') }}</span>
          <span class="text-lg font-semibold" :class="viewsResult.summary.deals?.kanban ? 'text-green-600' : 'text-red-600'">
            {{ viewsResult.summary.deals?.kanban ? __('Success') : __('Failed') }}
          </span>
        </div>
        <div class="flex flex-col gap-1">
          <span class="text-xs text-ink-gray-5">{{ __('Contact List') }}</span>
          <span class="text-lg font-semibold" :class="viewsResult.summary.contacts?.list ? 'text-green-600' : 'text-red-600'">
            {{ viewsResult.summary.contacts?.list ? __('Success') : __('Failed') }}
          </span>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Button, Badge, createResource, toast } from 'frappe-ui'
import LucideTrash2 from '~icons/lucide/trash-2'
import LucidePackage from '~icons/lucide/package'
import LucideRefreshCw from '~icons/lucide/refresh-cw'

const TrashIcon = LucideTrash2
const PackageIcon = LucidePackage
const RefreshCwIcon = LucideRefreshCw

const cleanResult = ref(null)
const productsResult = ref(null)
const viewsResult = ref(null)

const cleanDatabase = createResource({
  url: 'crm.api.products.reset_crm_database',
  method: 'POST',
  onSuccess: (result) => {
    cleanResult.value = result
    if (result.success) {
      toast.success(__('Database cleaned successfully!'))
    } else {
      toast.error(result.error || __('Error cleaning database'))
    }
  },
  onError: (error) => {
    toast.error(__('Error: ') + error.message)
    cleanResult.value = { success: false, error: error.message }
  }
})

const addProducts = createResource({
  url: 'crm.api.products.create_products',
  method: 'POST',
  onSuccess: (result) => {
    productsResult.value = result
    if (result.success) {
      toast.success(__('Products added successfully!'))
    } else {
      toast.error(result.error || __('Error adding products'))
    }
  },
  onError: (error) => {
    toast.error(__('Error: ') + error.message)
    productsResult.value = { success: false, error: error.message }
  }
})

const resetViews = createResource({
  url: 'crm.fcrm.doctype.crm_view_settings.crm_view_settings.reset_default_views',
  method: 'POST',
  onSuccess: (result) => {
    viewsResult.value = result
    if (result.success) {
      toast.success(__('Default views reset successfully!'))
    } else {
      toast.error(result.error || __('Error resetting views'))
    }
  },
  onError: (error) => {
    toast.error(__('Error: ') + error.message)
    viewsResult.value = { success: false, error: error.message }
  }
})

function handleCleanDatabase() {
  if (!confirm(
    __('⚠️ WARNING!\n\nThis will delete ALL operational data:\n') +
    __('• All Deals and Leads\n') +
    __('• All Contacts and Organizations\n') +
    __('• All Products and Tags\n') +
    __('• All Notes and Call Logs\n') +
    __('• All Tasks\n\n') +
    __('This action cannot be undone!\n\n') +
    __('Continue?')
  )) {
    return
  }

  cleanDatabase.fetch()
}

function handleAddProducts() {
  addProducts.fetch()
}

function handleResetViews() {
  if (!confirm(
    __('⚠️ Reset Default Views\n\n') +
    __('This will reset all default views (List and Kanban) for:\n') +
    __('• CRM Lead (List and Kanban)\n') +
    __('• CRM Deal (List and Kanban)\n') +
    __('• Contact (List)\n\n') +
    __('All views will be synchronized with the latest column definitions from the database.\n\n') +
    __('Continue?')
  )) {
    return
  }

  resetViews.fetch()
}
</script>

