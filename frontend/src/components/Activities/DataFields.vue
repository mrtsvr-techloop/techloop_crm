<template>
  <div
    class="my-3 flex items-center justify-between text-lg font-medium sm:mb-4 sm:mt-8"
  >
    <div class="flex h-8 items-center text-xl font-semibold text-ink-gray-8">
      {{ __('Data') }}
      <Badge
        v-if="document.isDirty"
        class="ml-3"
        :label="'Not Saved'"
        theme="orange"
      />
    </div>
    <div class="flex gap-1">
      <Button
        v-if="isManager() && !isMobileView"
        :tooltip="__('Edit fields layout')"
        :icon="EditIcon"
        @click="showDataFieldsModal = true"
      />
      <Button
        label="Save"
        :disabled="!document.isDirty"
        variant="solid"
        :loading="document.save.loading"
        @click="saveChanges"
      />
    </div>
  </div>
  <div
    v-if="document.get.loading"
    class="flex flex-1 flex-col items-center justify-center gap-3 text-xl font-medium text-ink-gray-6"
  >
    <LoadingIndicator class="h-6 w-6" />
    <span>{{ __('Loading...') }}</span>
  </div>
  <div v-else class="pb-8">
    <FieldLayout
      v-if="tabs.data"
      :tabs="tabs.data"
      :data="document.doc"
      :doctype="doctype"
    />
    
    <!-- Extra fields for CRM Deal after Products -->
    <div v-if="doctype === 'CRM Deal'" class="mt-6 space-y-6">
      <!-- Delivery Information Section -->
      <div class="border-t border-outline-gray-modals pt-6">
        <div class="text-base font-medium text-ink-gray-8 mb-4">{{ __('Delivery Information') }}</div>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm text-ink-gray-6 mb-2">{{ __('Delivery Date') }}</label>
            <input
              type="date"
              v-model="document.doc.delivery_date"
              class="w-full px-3 py-2 text-sm border border-outline-gray-1 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label class="block text-sm text-ink-gray-6 mb-2">{{ __('Delivery Address') }}</label>
            <textarea
              v-model="document.doc.delivery_address"
              rows="3"
              class="w-full px-3 py-2 text-sm border border-outline-gray-1 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              :placeholder="__('Enter delivery address...')"
            ></textarea>
          </div>
          <div>
            <label class="block text-sm text-ink-gray-6 mb-2">{{ __('Delivery Region') }}</label>
            <input
              type="text"
              v-model="document.doc.delivery_region"
              class="w-full px-3 py-2 text-sm border border-outline-gray-1 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              :placeholder="__('Enter delivery region...')"
            />
          </div>
          <div>
            <label class="block text-sm text-ink-gray-6 mb-2">{{ __('Delivery City') }}</label>
            <input
              type="text"
              v-model="document.doc.delivery_city"
              class="w-full px-3 py-2 text-sm border border-outline-gray-1 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              :placeholder="__('Enter delivery city...')"
            />
          </div>
          <div>
            <label class="block text-sm text-ink-gray-6 mb-2">{{ __('Delivery ZIP Code') }}</label>
            <input
              type="text"
              v-model="document.doc.delivery_zip"
              class="w-full px-3 py-2 text-sm border border-outline-gray-1 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              :placeholder="__('Enter delivery ZIP code...')"
            />
          </div>
        </div>
      </div>
      
      <!-- Order Notes Section -->
      <div class="border-t border-outline-gray-modals pt-6">
        <div class="text-base font-medium text-ink-gray-8 mb-4">{{ __('Order Notes') }}</div>
        <textarea
          v-model="document.doc.order_notes"
          rows="4"
          class="w-full px-3 py-2 text-sm border border-outline-gray-1 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
          :placeholder="__('Enter order notes...')"
        ></textarea>
      </div>
    </div>
  </div>
  <DataFieldsModal
    v-if="showDataFieldsModal"
    v-model="showDataFieldsModal"
    :doctype="doctype"
    @reload="
      () => {
        tabs.reload()
        document.reload()
      }
    "
  />
</template>

<script setup>
import EditIcon from '@/components/Icons/EditIcon.vue'
import DataFieldsModal from '@/components/Modals/DataFieldsModal.vue'
import FieldLayout from '@/components/FieldLayout/FieldLayout.vue'
import { Badge, createResource } from 'frappe-ui'
import LoadingIndicator from '@/components/Icons/LoadingIndicator.vue'
import { usersStore } from '@/stores/users'
import { useDocument } from '@/data/document'
import { isMobileView } from '@/composables/settings'
import { ref, watch, getCurrentInstance } from 'vue'

const props = defineProps({
  doctype: {
    type: String,
    required: true,
  },
  docname: {
    type: String,
    required: true,
  },
})

const emit = defineEmits(['beforeSave', 'afterSave'])

const { isManager } = usersStore()

const instance = getCurrentInstance()
const attrs = instance?.vnode?.props ?? {}

const showDataFieldsModal = ref(false)

const { document } = useDocument(props.doctype, props.docname)

const tabs = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_fields_layout',
  cache: ['DataFields', props.doctype],
  params: { doctype: props.doctype, type: 'Data Fields' },
  auto: true,
})

function saveChanges() {
  if (!document.isDirty) return

  const updatedDoc = { ...document.doc }
  const oldDoc = { ...document.originalDoc }

  const changes = Object.keys(updatedDoc).reduce((acc, key) => {
    if (JSON.stringify(updatedDoc[key]) !== JSON.stringify(oldDoc[key])) {
      acc[key] = updatedDoc[key]
    }
    return acc
  }, {})

  const hasListener = attrs['onBeforeSave'] !== undefined

  if (hasListener) {
    emit('beforeSave', changes)
  } else {
    document.save.submit(null, {
      onSuccess: () => emit('afterSave', changes),
    })
  }
}

watch(
  () => document.doc,
  (newValue, oldValue) => {
    if (!oldValue) return
    if (newValue && oldValue) {
      const isDirty =
        JSON.stringify(newValue) !== JSON.stringify(document.originalDoc)
      document.isDirty = isDirty
      if (isDirty) {
        document.save.loading = false
      }
    }
  },
  { deep: true },
)
</script>
