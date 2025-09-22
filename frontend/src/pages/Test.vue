<template>
  <div class="flex flex-col h-full overflow-hidden">
    <LayoutHeader>
      <template #left-header>
        <ViewBreadcrumbs routeName="Listino Prodotti" />
      </template>
      <template #right-header>
        <Button
          :label="__('Aggiorna')"
          :iconLeft="LucideRefreshCcw"
          @click="refreshProducts"
        />
        <Button
          variant="solid"
          :label="__('Aggiungi Prodotto')"
          :iconLeft="LucidePlus"
          @click="showAddModal = true"
        />
      </template>
    </LayoutHeader>

    <div class="p-5 flex-1 overflow-y-auto">
      <div class="mb-6">
        <h1 class="text-2xl font-semibold text-ink-gray-8 mb-2">
          {{ __('Listino Prodotti') }}
        </h1>
        <p class="text-ink-gray-6">
          {{ __('Gestisci il catalogo prodotti con prezzi e quantità.') }}
        </p>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
        <div class="bg-surface-gray-1 rounded-lg p-4">
          <div class="flex items-center gap-3 mb-2">
            <div class="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
              <LucidePackage class="w-4 h-4 text-blue-600" />
            </div>
            <h3 class="font-medium text-ink-gray-8">{{ __('Totale Prodotti') }}</h3>
          </div>
          <p class="text-2xl font-bold text-ink-gray-8">{{ products.length }}</p>
        </div>

        <div class="bg-surface-gray-1 rounded-lg p-4">
          <div class="flex items-center gap-3 mb-2">
            <div class="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
              <LucideEuro class="w-4 h-4 text-green-600" />
            </div>
            <h3 class="font-medium text-ink-gray-8">{{ __('Prezzo Medio') }}</h3>
          </div>
          <p class="text-2xl font-bold text-ink-gray-8">€{{ averagePrice }}</p>
        </div>

        <div class="bg-surface-gray-1 rounded-lg p-4">
          <div class="flex items-center gap-3 mb-2">
            <div class="w-8 h-8 bg-orange-100 rounded-full flex items-center justify-center">
              <LucideTrendingUp class="w-4 h-4 text-orange-600" />
            </div>
            <h3 class="font-medium text-ink-gray-8">{{ __('Valore Totale') }}</h3>
          </div>
          <p class="text-2xl font-bold text-ink-gray-8">€{{ totalValue }}</p>
        </div>
      </div>

      <!-- Search and Filter -->
      <div class="mb-6">
        <div class="flex gap-4 items-center">
          <div class="flex-1">
            <Input
              v-model="searchQuery"
              :placeholder="__('Cerca prodotti...')"
              :iconLeft="LucideSearch"
            />
          </div>
          <Dropdown
            v-model="sortBy"
            :options="sortOptions"
            :placeholder="__('Ordina per')"
            class="w-48"
          />
        </div>
      </div>

      <!-- Products Grid -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        <div
          v-for="product in filteredProducts"
          :key="product.name"
          class="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition-shadow cursor-pointer"
          @click="editProduct(product)"
        >
          <div class="flex items-start justify-between mb-3">
            <div class="flex items-center gap-3">
              <div class="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center flex-shrink-0">
                <img
                  v-if="product.image"
                  :src="product.image"
                  :alt="product.product_name"
                  class="w-8 h-8 object-cover rounded"
                />
                <LucidePackage v-else class="w-6 h-6 text-blue-600" />
              </div>
              <div class="min-w-0 flex-1">
                <h3 class="font-medium text-ink-gray-8 truncate">{{ product.product_name }}</h3>
                <p class="text-sm text-ink-gray-6 truncate">{{ product.product_code }}</p>
              </div>
            </div>
            <Button
              variant="ghost"
              size="sm"
              :iconLeft="LucideMoreVertical"
              @click.stop="showProductMenu(product)"
            />
          </div>
          
          <div class="space-y-2">
            <div class="flex justify-between items-center">
              <span class="text-sm text-ink-gray-6">{{ __('Prezzo:') }}</span>
              <span class="font-semibold text-ink-gray-8">€{{ product.rate || '0.00' }}</span>
            </div>
            <div class="flex justify-between items-center">
              <span class="text-sm text-ink-gray-6">{{ __('Quantità:') }}</span>
              <span class="font-medium text-ink-gray-8">{{ product.qty || 1 }}</span>
            </div>
            <div class="flex justify-between items-center border-t pt-2">
              <span class="text-sm font-medium text-ink-gray-8">{{ __('Totale:') }}</span>
              <span class="font-bold text-green-600">€{{ product.amount || '0.00' }}</span>
            </div>
          </div>

          <div v-if="product.description" class="mt-3 pt-3 border-t">
            <p class="text-xs text-ink-gray-6 line-clamp-2">{{ product.description }}</p>
          </div>
        </div>
      </div>

      <!-- Empty State -->
      <div v-if="filteredProducts.length === 0" class="text-center py-12">
        <LucidePackage class="w-16 h-16 mx-auto mb-4 text-ink-gray-4" />
        <h3 class="text-lg font-medium text-ink-gray-8 mb-2">{{ __('Nessun prodotto trovato') }}</h3>
        <p class="text-ink-gray-6 mb-4">{{ __('Inizia aggiungendo il tuo primo prodotto.') }}</p>
        <Button
          variant="solid"
          :label="__('Aggiungi Prodotto')"
          :iconLeft="LucidePlus"
          @click="showAddModal = true"
        />
      </div>
    </div>

    <!-- Add/Edit Product Modal -->
    <Dialog v-model="showAddModal" :options="{ title: isEditing ? __('Modifica Prodotto') : __('Aggiungi Prodotto') }">
      <template #body-content>
        <div class="space-y-4">
          <div class="grid grid-cols-2 gap-4">
            <Input
              v-model="productForm.product_code"
              :label="__('Codice Prodotto')"
              :placeholder="__('Es. PROD-001')"
              :disabled="isEditing"
            />
            <Input
              v-model="productForm.product_name"
              :label="__('Nome Prodotto')"
              :placeholder="__('Nome del prodotto')"
            />
          </div>
          
          <div class="grid grid-cols-2 gap-4">
            <Input
              v-model="productForm.rate"
              :label="__('Prezzo')"
              :placeholder="__('0.00')"
              type="number"
              step="0.01"
            />
            <Input
              v-model="productForm.qty"
              :label="__('Quantità')"
              :placeholder="__('1')"
              type="number"
              step="1"
            />
          </div>

          <Textarea
            v-model="productForm.description"
            :label="__('Descrizione')"
            :placeholder="__('Descrizione del prodotto')"
          />

          <div class="flex items-center gap-4">
            <Checkbox
              v-model="productForm.disabled"
              :label="__('Disabilitato')"
            />
          </div>
        </div>
      </template>
      <template #actions>
        <Button variant="ghost" :label="__('Annulla')" @click="closeModal" />
        <Button
          variant="solid"
          :label="isEditing ? __('Salva Modifiche') : __('Aggiungi Prodotto')"
          :disabled="!productForm.product_code || !productForm.product_name"
          :loading="saving"
          @click="saveProduct"
        />
      </template>
    </Dialog>

    <!-- Product Menu -->
    <Dialog v-model="showProductMenuModal" :options="{ title: __('Azioni Prodotto') }">
      <template #body-content>
        <div class="space-y-2">
          <Button
            variant="ghost"
            :label="__('Modifica')"
            :iconLeft="LucideEdit"
            @click="editProduct(selectedProduct)"
            class="w-full justify-start"
          />
          <Button
            variant="ghost"
            :label="__('Duplica')"
            :iconLeft="LucideCopy"
            @click="duplicateProduct(selectedProduct)"
            class="w-full justify-start"
          />
          <Button
            variant="ghost"
            :label="__('Elimina')"
            :iconLeft="LucideTrash2"
            @click="deleteProduct(selectedProduct)"
            class="w-full justify-start text-red-600"
          />
        </div>
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import LucideRefreshCcw from '~icons/lucide/refresh-ccw'
import LucidePlus from '~icons/lucide/plus'
import LucidePackage from '~icons/lucide/package'
import LucideEuro from '~icons/lucide/euro'
import LucideTrendingUp from '~icons/lucide/trending-up'
import LucideSearch from '~icons/lucide/search'
import LucideMoreVertical from '~icons/lucide/more-vertical'
import LucideEdit from '~icons/lucide/edit'
import LucideCopy from '~icons/lucide/copy'
import LucideTrash2 from '~icons/lucide/trash-2'
import { Button, Dialog, Input, Textarea, Dropdown, Checkbox, createResource, call } from 'frappe-ui'
import { ref, computed, watch } from 'vue'
import { usePageMeta } from 'frappe-ui'

// Reactive data
const products = ref([])
const showAddModal = ref(false)
const showProductMenuModal = ref(false)
const isEditing = ref(false)
const saving = ref(false)
const searchQuery = ref('')
const sortBy = ref('name')
const selectedProduct = ref(null)

// Product form
const productForm = ref({
  product_code: '',
  product_name: '',
  rate: '',
  qty: 1,
  description: '',
  disabled: false
})

// Sort options
const sortOptions = [
  { label: __('Nome'), value: 'name' },
  { label: __('Prezzo'), value: 'rate' },
  { label: __('Data Creazione'), value: 'creation' },
  { label: __('Codice'), value: 'code' }
]

// Computed properties
const filteredProducts = computed(() => {
  let filtered = products.value

  // Search filter
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(product => 
      product.product_name?.toLowerCase().includes(query) ||
      product.product_code?.toLowerCase().includes(query) ||
      product.description?.toLowerCase().includes(query)
    )
  }

  // Sort
  filtered.sort((a, b) => {
    switch (sortBy.value) {
      case 'name':
        return (a.product_name || '').localeCompare(b.product_name || '')
      case 'rate':
        return (b.rate || 0) - (a.rate || 0)
      case 'creation':
        return new Date(b.creation) - new Date(a.creation)
      case 'code':
        return (a.product_code || '').localeCompare(b.product_code || '')
      default:
        return 0
    }
  })

  return filtered
})

const averagePrice = computed(() => {
  if (products.value.length === 0) return '0.00'
  const total = products.value.reduce((sum, product) => sum + (product.rate || 0), 0)
  return (total / products.value.length).toFixed(2)
})

const totalValue = computed(() => {
  return products.value.reduce((sum, product) => {
    const amount = (product.rate || 0) * (product.qty || 1)
    return sum + amount
  }, 0).toFixed(2)
})

// Resources
const productsResource = createResource({
  url: 'frappe.client.get_list',
  makeParams() {
    return {
      doctype: 'CRM Product',
      fields: ['name', 'product_code', 'product_name', 'standard_rate', 'image', 'description', 'disabled', 'creation'],
      limit_page_length: 0
    }
  },
  auto: true,
  onSuccess(data) {
    products.value = data.map(product => ({
      ...product,
      rate: product.standard_rate || 0,
      qty: 1,
      amount: (product.standard_rate || 0) * 1
    }))
  }
})

// Methods
function refreshProducts() {
  productsResource.reload()
}

function closeModal() {
  showAddModal.value = false
  showProductMenuModal.value = false
  isEditing.value = false
  selectedProduct.value = null
  resetForm()
}

function resetForm() {
  productForm.value = {
    product_code: '',
    product_name: '',
    rate: '',
    qty: 1,
    description: '',
    disabled: false
  }
}

function editProduct(product) {
  isEditing.value = true
  selectedProduct.value = product
  productForm.value = {
    product_code: product.product_code,
    product_name: product.product_name,
    rate: product.rate,
    qty: product.qty,
    description: product.description || '',
    disabled: product.disabled || false
  }
  showAddModal.value = true
}

function showProductMenu(product) {
  selectedProduct.value = product
  showProductMenuModal.value = true
}

async function saveProduct() {
  if (!productForm.value.product_code || !productForm.value.product_name) return
  
  saving.value = true
  
  try {
    if (isEditing.value) {
      // Update existing product
      await call('frappe.client.set_value', {
        doctype: 'CRM Product',
        name: selectedProduct.value.name,
        fieldname: {
          product_name: productForm.value.product_name,
          standard_rate: parseFloat(productForm.value.rate) || 0,
          description: productForm.value.description,
          disabled: productForm.value.disabled
        }
      })
    } else {
      // Create new product
      const newProduct = await call('frappe.client.insert', {
        doc: {
          doctype: 'CRM Product',
          product_code: productForm.value.product_code,
          product_name: productForm.value.product_name,
          standard_rate: parseFloat(productForm.value.rate) || 0,
          description: productForm.value.description,
          disabled: productForm.value.disabled
        }
      })
      
      // Add to local products array
      products.value.push({
        name: newProduct.name,
        product_code: productForm.value.product_code,
        product_name: productForm.value.product_name,
        rate: parseFloat(productForm.value.rate) || 0,
        qty: parseInt(productForm.value.qty) || 1,
        amount: (parseFloat(productForm.value.rate) || 0) * (parseInt(productForm.value.qty) || 1),
        description: productForm.value.description,
        disabled: productForm.value.disabled,
        creation: new Date().toISOString()
      })
    }
    
    closeModal()
    refreshProducts()
  } catch (error) {
    console.error('Error saving product:', error)
  } finally {
    saving.value = false
  }
}

function duplicateProduct(product) {
  isEditing.value = false
  selectedProduct.value = null
  productForm.value = {
    product_code: `${product.product_code}-COPY`,
    product_name: `${product.product_name} (Copia)`,
    rate: product.rate,
    qty: product.qty,
    description: product.description || '',
    disabled: false
  }
  showProductMenuModal.value = false
  showAddModal.value = true
}

async function deleteProduct(product) {
  if (confirm(__('Sei sicuro di voler eliminare questo prodotto?'))) {
    try {
      await call('frappe.client.delete', {
        doctype: 'CRM Product',
        name: product.name
      })
      
      // Remove from local array
      const index = products.value.findIndex(p => p.name === product.name)
      if (index > -1) {
        products.value.splice(index, 1)
      }
      
      showProductMenuModal.value = false
    } catch (error) {
      console.error('Error deleting product:', error)
    }
  }
}

// Watch for form changes to calculate amount
watch(() => [productForm.value.rate, productForm.value.qty], () => {
  if (productForm.value.rate && productForm.value.qty) {
    productForm.value.amount = (parseFloat(productForm.value.rate) || 0) * (parseInt(productForm.value.qty) || 1)
  }
})

usePageMeta(() => {
  return { title: __('Listino Prodotti') }
})
</script>
