<template>
  <div class="flex flex-col flex-1 overflow-y-auto">
    <div class="px-3 pb-3 sm:px-10 sm:pb-5">
      <div class="my-3 flex items-center justify-between text-lg font-medium sm:mb-4 sm:mt-8">
        <div class="flex h-8 items-center text-lg font-semibold text-ink-gray-8">
          Prodotti ordinati
        </div>
        <button 
          @click="addProduct" 
          class="px-3 py-1.5 text-sm bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
        >
          + Aggiungi Prodotto
        </button>
      </div>
      
      <!-- Tabella Custom -->
      <div class="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <table class="w-full text-sm">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-2 py-2 text-left text-xs font-medium text-gray-700">Prodotto</th>
              <th class="px-2 py-2 text-left text-xs font-medium text-gray-700">Quantità</th>
              <th class="px-2 py-2 text-left text-xs font-medium text-gray-700">Prezzo</th>
              <th class="px-2 py-2 text-left text-xs font-medium text-gray-700">Sconto</th>
              <th class="px-2 py-2 text-left text-xs font-medium text-gray-700">Totale</th>
              <th class="px-2 py-2 text-left text-xs font-medium text-gray-700">Azione</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-200">
            <tr v-for="(product, index) in products" :key="index" class="hover:bg-gray-50">
              <td class="px-2 py-2">
                <select 
                  v-model="product.product_code" 
                  @change="onProductChange(index)"
                  class="w-full px-2 py-1.5 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                >
                  <option value="">Seleziona prodotto</option>
                  <option v-for="prod in availableProducts" :key="prod.name" :value="prod.name">
                    {{ prod.product_name }} ({{ prod.name }})
                  </option>
                </select>
              </td>
              <td class="px-2 py-2">
                <input 
                  type="number" 
                  v-model.number="product.qty" 
                  @input="calculateTotals(index)"
                  min="1"
                  class="w-full px-2 py-1.5 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
              </td>
              <td class="px-2 py-2">
                <input 
                  type="number" 
                  v-model.number="product.rate" 
                  @input="calculateTotals(index)"
                  step="0.01"
                  min="0"
                  class="w-full px-2 py-1.5 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
              </td>
              <td class="px-2 py-2">
                <div class="relative">
                  <input 
                    type="number" 
                    v-model.number="product.discount_percentage" 
                    @input="calculateTotals(index)"
                    step="0.01"
                    min="0"
                    max="100"
                    class="w-full px-2 py-1.5 pr-6 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                  />
                  <span class="absolute right-1.5 top-1/2 transform -translate-y-1/2 text-gray-500 text-xs">%</span>
                </div>
              </td>
              <td class="px-2 py-2">
                <span class="font-medium text-sm">{{ formatCurrency(product.amount || 0, '', 'EUR') }}</span>
              </td>
              <td class="px-2 py-2">
                <button 
                  @click="removeProduct(index)"
                  class="px-2 py-1 text-xs bg-red-500 text-white rounded hover:bg-red-600 transition-colors"
                >
                  Rimuovi
                </button>
              </td>
            </tr>
          </tbody>
        </table>
        
        <!-- Stato vuoto -->
        <div v-if="products.length === 0" class="p-8 text-center text-gray-500">
          <ProductsIcon class="h-12 w-12 mx-auto mb-4 text-gray-300" />
          <p>Nessun prodotto aggiunto</p>
          <p class="text-sm">Clicca "Aggiungi Prodotto" per iniziare</p>
        </div>
      </div>
      
      <!-- Totali e Dettagli Consegna -->
      <div v-if="products.length > 0" class="mt-6 bg-gray-50 rounded-lg p-4">
        <div class="flex justify-between items-start gap-6">
          <!-- Sinistra: Dettagli Consegna -->
          <div class="flex flex-col gap-3">
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
          
          <!-- Destra: Totali -->
          <div class="flex gap-6 text-lg font-semibold">
            <div class="text-center">
              <div class="text-sm text-gray-600">Totale</div>
              <div class="text-xl text-gray-900">{{ formatCurrency(total, '', 'EUR') }}</div>
            </div>
            <div class="text-center">
              <div class="text-sm text-gray-600">Totale Netto</div>
              <div class="text-xl text-gray-900">{{ formatCurrency(netTotal, '', 'EUR') }}</div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Note Ordine -->
      <div v-if="orderNotes" class="mt-6 bg-blue-50 rounded-lg p-4 border border-blue-200">
        <div class="text-sm font-semibold text-blue-900 mb-2">📝 Note</div>
        <div class="text-sm text-gray-700 whitespace-pre-wrap">{{ orderNotes }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { createResource } from 'frappe-ui'
import ProductsIcon from '@/components/Icons/ProductsIcon.vue'
import { formatCurrency } from '@/utils/numberFormat'

// Disabilita completamente i toast per questa pagina
let originalToastFunction = null
let originalMessageFunction = null
let originalMsgprintFunction = null

// Debounce per evitare troppi aggiornamenti
let updateTimeout = null

const props = defineProps({
  doc: {
    type: Object,
    required: true,
  },
})

const emit = defineEmits(['update'])

// Prodotti dal documento
const products = ref(props.doc.products || [])

// Watch per aggiornare i prodotti quando il documento si carica
watch(() => props.doc.products, (newProducts) => {
  if (newProducts && newProducts.length > 0 && products.value.length === 0) {
    products.value = newProducts
  }
}, { immediate: true, deep: true })

// Resource per caricare i prodotti disponibili
const productsResource = createResource({
  url: 'crm.fcrm.doctype.crm_product.crm_product.get_products_for_selection',
  cache: ['crm_products_for_selection'],
  auto: true,
})

const availableProducts = computed(() => {
  return productsResource.data || []
})

const total = computed(() => {
  return products.value.reduce((sum, product) => sum + (product.amount || 0), 0)
})

const netTotal = computed(() => {
  return products.value.reduce((sum, product) => sum + (product.net_amount || product.amount || 0), 0)
})

// Estrai note dal custom_order_details
const orderNotes = computed(() => {
  if (!props.doc.custom_order_details) return null
  
  try {
    const orderDetails = typeof props.doc.custom_order_details === 'string' 
      ? JSON.parse(props.doc.custom_order_details) 
      : props.doc.custom_order_details
    
    return orderDetails?.notes || null
  } catch (e) {
    console.error('Error parsing custom_order_details:', e)
    return null
  }
})

const deliveryDate = computed(() => {
  if (!props.doc.custom_order_details) return null
  try {
    const orderDetails = typeof props.doc.custom_order_details === 'string'
      ? JSON.parse(props.doc.custom_order_details)
      : props.doc.custom_order_details
    return orderDetails?.delivery_date || props.doc.delivery_date || null
  } catch (e) {
    return props.doc.delivery_date || null
  }
})

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

function addProduct() {
  products.value.push({
    product_code: '',
    product_name: '',
    qty: 1,
    rate: 0,
    discount_percentage: 0,
    amount: 0,
    net_amount: 0
  })
  emit('update', products.value)
}

function removeProduct(index) {
  products.value.splice(index, 1)
  emit('update', products.value)
}

function onProductChange(index) {
  const product = products.value[index]
  const selectedProduct = availableProducts.value.find(p => p.name === product.product_code)
  
  if (selectedProduct) {
    product.product_name = selectedProduct.product_name
    product.rate = selectedProduct.standard_rate || 0
    calculateTotals(index)
  }
}

function calculateTotals(index) {
  const product = products.value[index]
  
  // Calcola amount (quantità × prezzo)
  product.amount = (product.qty || 0) * (product.rate || 0)
  
  // Calcola discount_amount
  const discountAmount = product.amount * ((product.discount_percentage || 0) / 100)
  
  // Calcola net_amount (amount - discount)
  product.net_amount = product.amount - discountAmount
  
  // Debounce per evitare troppi aggiornamenti rapidi
  if (updateTimeout) {
    clearTimeout(updateTimeout)
  }
  updateTimeout = setTimeout(() => {
    emit('update', products.value)
  }, 300) // 300ms di delay
}

onMounted(() => {
  // Disabilita completamente i toast per questa pagina
  if (window.frappe) {
    // Salva le funzioni originali
    originalToastFunction = window.frappe.show_alert
    originalMessageFunction = window.frappe.show_message
    originalMsgprintFunction = window.frappe.msgprint
    
    // Sostituisci con funzioni vuote
    window.frappe.show_alert = () => {}
    window.frappe.show_message = () => {}
    window.frappe.msgprint = () => {}
  }
  
  // Disabilita anche i toast di Frappe UI se disponibili
  if (window.frappe && window.frappe.ui && window.frappe.ui.show_alert) {
    window.frappe.ui.show_alert = () => {}
  }
  
  if (props.doc.products) {
    products.value = [...props.doc.products]
  }
})

onUnmounted(() => {
  // Ripristina le funzioni originali quando il componente viene distrutto
  if (window.frappe && originalToastFunction) {
    window.frappe.show_alert = originalToastFunction
    window.frappe.show_message = originalMessageFunction
    window.frappe.msgprint = originalMsgprintFunction
  }
})
</script>
