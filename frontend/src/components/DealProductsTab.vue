<template>
  <div class="flex flex-col flex-1 overflow-y-auto">
    <div class="px-3 pb-3 sm:px-10 sm:pb-5">
      <div class="my-3 flex items-center text-lg font-medium sm:mb-4 sm:mt-8">
        <div class="flex h-8 items-center text-lg font-semibold text-ink-gray-8">
          📦 Dettagli Ordine
        </div>
      </div>

      <!-- Dettagli Consegna -->
      <div class="bg-gray-50 rounded-lg p-6">
        <div class="mb-4">
          <h3 class="text-lg font-semibold text-gray-900 mb-4">🏠 Informazioni Consegna</h3>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div v-if="deliveryRegion">
              <div class="text-sm text-gray-600 font-medium">Regione</div>
              <div class="text-base text-gray-900">{{ deliveryRegion }}</div>
            </div>
            <div v-if="deliveryCity">
              <div class="text-sm text-gray-600 font-medium">Città</div>
              <div class="text-base text-gray-900">{{ deliveryCity }}</div>
            </div>
            <div v-if="deliveryZip">
              <div class="text-sm text-gray-600 font-medium">CAP</div>
              <div class="text-base text-gray-900">{{ deliveryZip }}</div>
            </div>
            <div v-if="deliveryAddress">
              <div class="text-sm text-gray-600 font-medium">Indirizzo di Consegna</div>
              <div class="text-base text-gray-900">{{ deliveryAddress }}</div>
            </div>
            <div v-if="deliveryDate">
              <div class="text-sm text-gray-600 font-medium">Data di Consegna</div>
              <div class="text-base text-gray-900">{{ deliveryDate }}</div>
            </div>
          </div>
        </div>

        <!-- Informazioni aggiuntive -->
        <div v-if="orderNotes || orderDate" class="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
          <div v-if="orderDate" class="bg-white p-4 rounded-lg border border-gray-200">
            <div class="text-sm text-gray-600 font-medium mb-1">📅 Data Ordine</div>
            <div class="text-base text-gray-900">{{ orderDate }}</div>
          </div>
          <div v-if="orderNotes" class="bg-white p-4 rounded-lg border border-gray-200 md:col-span-2">
            <div class="text-sm text-gray-600 font-medium mb-1">📝 Note Ordine</div>
            <div class="text-base text-gray-900 whitespace-pre-wrap">{{ orderNotes }}</div>
          </div>
        </div>

        <!-- Stato Deal -->
        <div v-if="dealStatus" class="mt-6">
          <div class="bg-white p-4 rounded-lg border border-gray-200">
            <div class="text-sm text-gray-600 font-medium mb-1">📊 Stato Deal</div>
            <div class="text-base text-gray-900">{{ dealStatus }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  doc: {
    type: Object,
    required: true,
  },
})

// Computed properties for delivery information
const deliveryAddress = computed(() => {
  return props.doc.delivery_address || null
})

const deliveryRegion = computed(() => {
  return props.doc.delivery_region || null
})

const deliveryCity = computed(() => {
  return props.doc.delivery_city || null
})

const deliveryZip = computed(() => {
  return props.doc.delivery_zip || null
})

const deliveryDate = computed(() => {
  // First try direct field, then custom_order_details
  if (props.doc.delivery_date) return props.doc.delivery_date

  if (!props.doc.custom_order_details) return null
  try {
    const orderDetails = typeof props.doc.custom_order_details === 'string'
      ? JSON.parse(props.doc.custom_order_details)
      : props.doc.custom_order_details
    return orderDetails?.delivery_date || null
  } catch (e) {
    return props.doc.delivery_date || null
  }
})

const orderDate = computed(() => {
  return props.doc.order_date || null
})

const orderNotes = computed(() => {
  // First try direct field, then custom_order_details
  if (props.doc.order_notes) return props.doc.order_notes

  if (!props.doc.custom_order_details) return null
  try {
    const orderDetails = typeof props.doc.custom_order_details === 'string'
      ? JSON.parse(props.doc.custom_order_details)
      : props.doc.custom_order_details
    return orderDetails?.notes || null
  } catch (e) {
    return null
  }
})

const dealStatus = computed(() => {
  return props.doc.status || null
})
</script>
