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
          @click="addNewProduct"
        />
      </template>
    </LayoutHeader>

    <div class="p-5 flex-1 overflow-y-auto">
      <div class="mb-6">
        <h1 class="text-2xl font-semibold text-ink-gray-8 mb-2">
          {{ __('Listino Prodotti') }}
        </h1>
        <p class="text-ink-gray-6">
          {{ __('Gestisci il catalogo prodotti con prezzi.') }}
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
          <Button
            variant="outline"
            :iconLeft="LucideFilter"
            :label="getFilterButtonLabel()"
            @click="showFilterModal = true"
          />
        </div>
        
        <!-- Filter Status -->
        <div v-if="hasActiveFilters" class="mt-3 flex items-center gap-2">
          <span class="text-sm text-ink-gray-6">{{ __('Vista filtrata:') }}</span>
          <Badge
            v-if="selectedTag"
            :label="`Tag: ${selectedTag}`"
            variant="subtle"
          />
          <Badge
            v-if="sortBy !== 'name'"
            :label="`Ordinato per: ${getSortLabel()}`"
            variant="subtle"
          />
          <Button
            variant="ghost"
            size="sm"
            :label="__('Rimuovi filtri')"
            @click="clearFilters"
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
            <div class="flex justify-between items-center border-t pt-2">
              <span class="text-sm font-medium text-ink-gray-8">{{ __('Prezzo:') }}</span>
              <span class="font-bold text-green-600">€{{ (product.rate || 0).toFixed(2) }}</span>
            </div>
          </div>

          <div v-if="product.description" class="mt-3 pt-3 border-t">
            <p class="text-xs text-ink-gray-6 line-clamp-2">{{ product.description }}</p>
          </div>

          <div v-if="product.product_tags && product.product_tags.length > 0" class="mt-3 pt-3 border-t">
            <div class="flex flex-wrap gap-1">
              <span
                v-for="tagRow in product.product_tags"
                :key="tagRow.tag_name"
                class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
              >
                {{ tagRow.tag_name }}
              </span>
            </div>
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
          @click="addNewProduct"
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
          
          <Input
            v-model="productForm.rate"
            :label="__('Prezzo')"
            :placeholder="__('0.00')"
            type="number"
            step="0.01"
          />

          <Textarea
            v-model="productForm.description"
            :label="__('Descrizione')"
            :placeholder="__('Descrizione del prodotto')"
          />

          <div>
            <label class="block text-sm font-medium text-ink-gray-8 mb-2">{{ __('Tags') }}</label>
            <div class="space-y-2">
              <div v-for="(tagRow, index) in productForm.product_tags" :key="index" class="flex items-center gap-2">
                <Input
                  v-model="tagRow.tag_name"
                  :placeholder="__('Nome tag')"
                  class="flex-1"
                />
                <Button
                  variant="ghost"
                  size="sm"
                  :iconLeft="LucideTrash2"
                  @click="removeTag(index)"
                />
              </div>
              <Button
                variant="outline"
                size="sm"
                :iconLeft="LucidePlus"
                :label="__('Aggiungi Tag')"
                @click="addTag"
              />
            </div>
          </div>

          <div class="flex items-center gap-4">
            <Checkbox
              v-model="productForm.disabled"
              :label="__('Disabilitato')"
            />
          </div>
        </div>
      </template>
      <template #actions>
        <div class="flex gap-2 ml-auto">
          <Button variant="ghost" :label="__('Annulla')" @click="closeModal" />
          <Button
            variant="solid"
            :label="isEditing ? __('Salva Modifiche') : __('Aggiungi Prodotto')"
            :disabled="!productForm.product_code || !productForm.product_name"
            :loading="saving"
            @click="saveProduct"
          />
        </div>
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
            @click="editProductFromMenu(selectedProduct)"
            class="w-full justify-start"
          />
          <Button
            variant="ghost"
            :label="__('Duplica')"
            :iconLeft="LucideCopy"
            @click="duplicateProductFromMenu(selectedProduct)"
            class="w-full justify-start"
          />
          <Button
            variant="ghost"
            :label="__('Elimina')"
            :iconLeft="LucideTrash2"
            @click="deleteProductFromMenu(selectedProduct)"
            class="w-full justify-start text-red-600"
          />
        </div>
      </template>
    </Dialog>

    <!-- Filter Modal -->
    <Dialog v-model="showFilterModal" :options="{ title: __('Filtri e Ordinamento') }">
      <template #body-content>
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-ink-gray-8 mb-2">{{ __('Filtra per Tag') }}</label>
            <Dropdown
              v-model="selectedTag"
              :options="tagFilterOptions"
              :placeholder="__('Seleziona un tag')"
              @change="applyFilters"
            />
          </div>
          
          <div>
            <label class="block text-sm font-medium text-ink-gray-8 mb-2">{{ __('Ordina per') }}</label>
            <Dropdown
              v-model="sortBy"
              :options="sortOptions"
              :placeholder="__('Seleziona ordinamento')"
              @change="applyFilters"
            />
          </div>
        </div>
      </template>
      <template #actions>
        <div class="flex gap-2 ml-auto">
          <Button variant="solid" :label="__('Chiudi')" @click="showFilterModal = false" />
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
import LucideFilter from '~icons/lucide/filter'
import { Button, Dialog, Input, Textarea, Dropdown, Checkbox, Badge, createResource, call } from 'frappe-ui'
import { ref, computed } from 'vue'
import { usePageMeta } from 'frappe-ui'

// Reactive data
const products = ref([])
const showAddModal = ref(false)
const showProductMenuModal = ref(false)
const showFilterModal = ref(false)
const isEditing = ref(false)
const saving = ref(false)
const searchQuery = ref('')
const sortBy = ref('name')
const selectedTag = ref('')
const selectedProduct = ref(null)


// Product form
const productForm = ref({
  product_code: '',
  product_name: '',
  rate: '',
  description: '',
  product_tags: [],
  disabled: false
})

// Sort options
const sortOptions = [
  { label: __('Nome'), value: 'name' },
  { label: __('Prezzo'), value: 'rate' },
  { label: __('Data Creazione'), value: 'creation' },
  { label: __('Codice'), value: 'code' }
]

// Tag filter options
const tagFilterOptions = computed(() => {
  const allTags = new Set()
  products.value.forEach(product => {
    if (product.product_tags && product.product_tags.length > 0) {
      product.product_tags.forEach(tagRow => {
        if (tagRow.tag_name) allTags.add(tagRow.tag_name)
      })
    }
  })
  
  const options = [{ label: __('Tutti i tag'), value: '' }]
  Array.from(allTags).sort().forEach(tag => {
    options.push({ label: tag, value: tag })
  })
  return options
})

// Computed properties
const filteredProducts = computed(() => {
  let filtered = products.value

  // Search filter
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(product => {
      const searchInTags = product.product_tags?.some(tagRow => 
        tagRow.tag_name?.toLowerCase().includes(query)
      ) || false
      
      return product.product_name?.toLowerCase().includes(query) ||
             product.product_code?.toLowerCase().includes(query) ||
             product.description?.toLowerCase().includes(query) ||
             searchInTags
    })
  }

  // Tag filter
  if (selectedTag.value) {
    filtered = filtered.filter(product => {
      if (!product.product_tags || product.product_tags.length === 0) return false
      return product.product_tags.some(tagRow => tagRow.tag_name === selectedTag.value)
    })
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
    return sum + (product.rate || 0)
  }, 0).toFixed(2)
})

// Filter and sorting helpers
const hasActiveFilters = computed(() => {
  return selectedTag.value || sortBy.value !== 'name'
})

const getFilterButtonLabel = () => {
  if (hasActiveFilters.value) {
    return __('Filtri Attivi')
  }
  return __('Filtri')
}

const getSortLabel = () => {
  const option = sortOptions.find(opt => opt.value === sortBy.value)
  return option ? option.label : ''
}

// Resources
const productsResource = createResource({
  url: 'frappe.client.get_list',
  makeParams() {
    return {
      doctype: 'CRM Product',
      fields: ['name', 'product_code', 'product_name', 'standard_rate', 'image', 'description', 'disabled', 'creation', 'product_tags'],
      limit_page_length: 0
    }
  },
  auto: true,
  onSuccess(data) {
    // Load product tags for each product
    const promises = data.map(async product => {
      if (product.name) {
        try {
          const tagData = await call('frappe.client.get_list', {
            doctype: 'CRM Product Tag',
            filters: { parent: product.name },
            fields: ['tag_name']
          })
          return {
            ...product,
            rate: product.standard_rate || 0,
            product_tags: tagData || []
          }
        } catch (error) {
          console.error('Error loading tags for product:', product.name, error)
          return {
            ...product,
            rate: product.standard_rate || 0,
            product_tags: []
          }
        }
      }
      return {
        ...product,
        rate: product.standard_rate || 0,
        product_tags: []
      }
    })
    
    Promise.all(promises).then(productsWithTags => {
      products.value = productsWithTags
    })
  }
})



// Methods
function refreshProducts() {
  productsResource.reload()
}

function addNewProduct() {
  isEditing.value = false
  selectedProduct.value = null
  resetForm()
  showAddModal.value = true
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
    description: '',
    product_tags: [],
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
    description: product.description || '',
    product_tags: product.product_tags ? [...product.product_tags] : [],
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
    const productData = {
      product_name: productForm.value.product_name,
      standard_rate: parseFloat(productForm.value.rate) || 0,
      description: productForm.value.description,
      disabled: productForm.value.disabled,
      product_tags: productForm.value.product_tags
    }

    if (isEditing.value && selectedProduct.value) {
      // Update existing product using full document update to handle child table
      const doc = await call('frappe.client.get_doc', {
        doctype: 'CRM Product',
        name: selectedProduct.value.name
      })
      
      // Update the document with new values
      Object.assign(doc, productData)
      
      await call('frappe.client.save', {
        doc: doc
      })
    } else {
      // Create new product
      const newProduct = await call('frappe.client.insert', {
        doc: {
          doctype: 'CRM Product',
          product_code: productForm.value.product_code,
          ...productData
        }
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
    description: product.description || '',
    product_tags: product.product_tags ? [...product.product_tags] : [],
    disabled: false
  }
  showProductMenuModal.value = false
  showAddModal.value = true
}

function editProductFromMenu(product) {
  showProductMenuModal.value = false
  editProduct(product)
}

function duplicateProductFromMenu(product) {
  showProductMenuModal.value = false
  duplicateProduct(product)
}

async function deleteProductFromMenu(product) {
  showProductMenuModal.value = false
  await deleteProduct(product)
}

function getProductTags(tagsString) {
  if (!tagsString) return []
  return tagsString.split(',').map(tag => tag.trim()).filter(tag => tag.length > 0)
}

function addTag() {
  productForm.value.product_tags.push({
    tag_name: ''
  })
}

function removeTag(index) {
  productForm.value.product_tags.splice(index, 1)
}

function applyFilters() {
  showFilterModal.value = false
}

function clearFilters() {
  selectedTag.value = ''
  sortBy.value = 'name'
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
      let errorMessage = __('Impossibile eliminare il prodotto.')
      
      if (error.message) {
        if (error.message.includes('linked') || error.message.includes('referenced')) {
          errorMessage = __('Impossibile eliminare il prodotto perché è utilizzato in altri documenti. Rimuovi prima tutti i riferimenti a questo prodotto.')
        } else if (error.message.includes('permission')) {
          errorMessage = __('Non hai i permessi necessari per eliminare questo prodotto.')
        } else if (error.message.includes('not found')) {
          errorMessage = __('Il prodotto non esiste più nel sistema.')
        }
      }
      
      alert(errorMessage)
      showProductMenuModal.value = false
    }
  }
}


usePageMeta(() => {
  return { title: __('Listino Prodotti') }
})
</script>
