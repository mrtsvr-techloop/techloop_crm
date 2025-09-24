<template>
  <div class="flex flex-col h-full overflow-hidden">
    <LayoutHeader>
      <template #left-header>
        <ViewBreadcrumbs routeName="Listino Prodotti" />
      </template>
      <template #right-header>
        <Button :label="__('Aggiorna')" :iconLeft="LucideRefreshCcw" @click="refreshProducts" />
        <Button variant="solid" :label="__('Aggiungi Prodotto')" :iconLeft="LucidePlus" @click="addNewProduct" />
      </template>
    </LayoutHeader>

    <div class="p-5 flex-1 overflow-y-auto">
      <div class="mb-6">
        <p class="text-ink-gray-6">{{ __('Gestisci il catalogo prodotti con prezzi.') }}</p>
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

      <div class="mb-6">
        <div class="flex gap-3 items-center">
          <div class="flex-1">
            <Input v-model="searchQuery" :placeholder="__('Cerca prodotti...')" :iconLeft="LucideSearch" />
          </div>
          <Button size="sm" variant="outline" :label="__('Tutti')" @click="sortBy='name'" />
          <Button size="sm" variant="outline" :label="__('Prezzo')" @click="sortBy='rate'" />
          <Button size="sm" variant="outline" :label="__('Data')" @click="sortBy='creation'" />
          <Button size="sm" variant="outline" :label="__('Codice')" @click="sortBy='code'" />
        </div>
        <div v-if="hasActiveFilters" class="mt-3 flex items-center gap-2">
          <span class="text-sm text-ink-gray-6">{{ __('Vista filtrata:') }}</span>
          <Badge v-if="sortBy !== 'name'" :label="`Ordinato per: ${getSortLabel()}`" variant="subtle" />
          <Button variant="ghost" size="sm" :label="__('Rimuovi filtri')" @click="clearFilters" />
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        <div v-for="product in filteredProducts" :key="product.name" class="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition-shadow cursor-pointer" @click="editProduct(product)">
          <div class="flex items-start justify-between mb-3">
            <div class="flex items-center gap-3">
              <div class="w-12 h-12 rounded-lg flex items-center justify-center flex-shrink-0" :class="product.disabled ? 'bg-gray-100' : 'bg-blue-100'">
                <img v-if="product.image" :src="product.image" :alt="product.product_name" class="w-8 h-8 object-cover rounded" />
                <LucidePackage v-else :class="product.disabled ? 'w-6 h-6 text-gray-400' : 'w-6 h-6 text-blue-600'" />
              </div>
              <div class="min-w-0 flex-1">
                <h3 class="font-medium truncate" :class="product.disabled ? 'text-ink-gray-5' : 'text-ink-gray-8'">{{ product.product_name }}</h3>
                <p class="text-sm truncate" :class="product.disabled ? 'text-ink-gray-4' : 'text-ink-gray-6'">{{ product.product_code }}</p>
              </div>
              <Badge v-if="product.disabled" :label="__('Non disponibile')" />
            </div>
            <Button variant="ghost" size="sm" :iconLeft="LucideMoreVertical" @click.stop="showProductMenu(product)" />
          </div>
          <div class="space-y-2">
            <div class="flex justify-between items-center border-t pt-2">
              <span class="text-sm font-medium text-ink-gray-8">{{ __('Prezzo:') }}</span>
              <span class="font-bold text-green-600">€{{ (product.rate || 0).toFixed(2) }}</span>
            </div>
          </div>
          <div v-if="product.description" class="mt-3 pt-3 border-t">
            <p class="text-xs line-clamp-2" :class="product.disabled ? 'text-ink-gray-4' : 'text-ink-gray-6'">{{ product.description }}</p>
          </div>
          <div v-if="product.product_tags && product.product_tags.length > 0" class="mt-3 pt-3 border-t">
            <div class="flex flex-wrap gap-1">
              <span v-for="tagRow in product.product_tags" :key="tagRow.tag_name" class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium" :style="{ backgroundColor: tagRow.color || '#e0f2fe', color: getReadableTextColor(tagRow.color || '#e0f2fe') }">{{ tagRow.tag_name }}</span>
            </div>
          </div>
        </div>
      </div>

      <div v-if="filteredProducts.length === 0" class="text-center py-12">
        <LucidePackage class="w-16 h-16 mx-auto mb-4 text-ink-gray-4" />
        <h3 class="text-lg font-medium text-ink-gray-8 mb-2">{{ __('Nessun prodotto trovato') }}</h3>
        <p class="text-ink-gray-6 mb-4">{{ __('Inizia aggiungendo il tuo primo prodotto.') }}</p>
        <Button variant="solid" :label="__('Aggiungi Prodotto')" :iconLeft="LucidePlus" @click="addNewProduct" />
      </div>
    </div>

    <Dialog v-model="showAddModal" :options="{ title: isEditing ? __('Modifica Prodotto') : __('Aggiungi Prodotto') }">
      <template #body-content>
        <div class="space-y-4">
          <div class="flex gap-4 items-start">
            <div>
              <label class="block text-sm font-medium text-ink-gray-8 mb-2">{{ __('Immagine') }}</label>
              <div class="w-24 h-24 rounded border flex items-center justify-center bg-white overflow-hidden">
                <img v-if="productForm.image" :src="productForm.image" :alt="productForm.product_name" class="w-full h-full object-cover" />
                <LucidePackage v-else class="w-8 h-8 text-ink-gray-4" />
              </div>
              <div class="mt-2 flex gap-2">
                <FileUploader :fileTypes="'image/*'" @success="onImageUploaded">
                  <template #default="{ openFileSelector, uploading, progress }">
                    <Button size="sm" variant="outline" :label="productForm.image ? __('Cambia') : __('Aggiungi')" @click="openFileSelector" />
                    <span v-if="uploading" class="text-xs text-ink-gray-5">{{ progress }}%</span>
                  </template>
                </FileUploader>
                <Button v-if="productForm.image" size="sm" variant="ghost" :label="__('Rimuovi')" @click="removeImage()" />
              </div>
            </div>
            <div class="flex-1 grid gap-3">
              <Input v-model="productForm.product_name" :label="__('Nome Prodotto')" :placeholder="__('Nome del prodotto')" />
              <Input v-model="productForm.product_code" :label="__('Codice Prodotto')" :placeholder="__('Es. PROD-001')" :disabled="isEditing" />
            </div>
          </div>
          <Input v-model="productForm.rate" :label="__('Prezzo')" :placeholder="__('0.00')" type="number" step="0.01" />
          <Textarea v-model="productForm.description" :label="__('Descrizione')" :placeholder="__('Descrizione del prodotto')" />
          <div>
            <label class="block text-sm font-medium text-ink-gray-8 mb-2">{{ __('Etichette') }}</label>
            <div class="border border-gray-200 rounded-lg overflow-hidden">
              <table class="w-full">
                <thead class="bg-gray-50"><tr><th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">{{ __('Etichetta') }}</th><th class="w-16 px-4 py-2"></th></tr></thead>
                <tbody>
                  <tr v-for="(tagRow, index) in productForm.product_tags" :key="index" class="border-t border-gray-200">
                    <td class="px-4 py-2">
                      <div class="flex items-center gap-2">
                        <Link v-model="tagRow.tag_name" doctype="CRM Product Tag Master" :placeholder="__('Seleziona o crea etichetta')" :onCreate="async (value, close) => { await createNewTag(value, tagRow); close() }" class="flex-1" />
                        <input type="color" v-model="tagRow.color" class="w-8 h-8 p-0 rounded-full appearance-none bg-transparent border-0 outline-none" />
                      </div>
                    </td>
                    <td class="px-4 py-2"><Button variant="ghost" size="sm" icon="trash-2" @click="removeTag(index)" /></td>
                  </tr>
                  <tr v-if="productForm.product_tags.length === 0"><td colspan="2" class="px-4 py-8 text-center text-gray-500 text-sm">{{ __('Nessun tag aggiunto') }}</td></tr>
                </tbody>
              </table>
              <div class="px-4 py-2 border-t border-gray-200 bg-gray-50"><Button variant="ghost" size="sm" icon="plus" :label="__('Aggiungi Riga')" @click="addTag" /></div>
            </div>
          </div>
          <div class="flex items-center gap-4"><Checkbox v-model="productForm.disabled" :label="__('Non disponibile')" /></div>
        </div>
      </template>
      <template #actions>
        <div class="flex gap-2 ml-auto"><Button variant="ghost" :label="__('Annulla')" @click="closeModal" /><Button variant="solid" :label="isEditing ? __('Salva Modifiche') : __('Aggiungi Prodotto')" :disabled="!productForm.product_code || !productForm.product_name" :loading="saving" @click="saveProduct" /></div>
      </template>
    </Dialog>

    <Dialog v-model="showProductMenuModal" :options="{ title: __('Azioni Prodotto') }">
      <template #body-content>
        <div class="space-y-2">
          <Button variant="ghost" :label="__('Modifica')" :iconLeft="LucideEdit" @click="editProductFromMenu(selectedProduct)" class="w-full justify-start" />
          <Button variant="ghost" :label="__('Elimina')" :iconLeft="LucideTrash2" @click="deleteProductFromMenu(selectedProduct)" class="w-full justify-start text-red-600" />
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
import LucideTrash2 from '~icons/lucide/trash-2'
import { Button, Dialog, Input, Textarea, Checkbox, Badge, FileUploader, createResource, call } from 'frappe-ui'
import Link from '@/components/Controls/Link.vue'
import { ref, computed } from 'vue'
import { usePageMeta } from 'frappe-ui'

const products = ref([])
const showAddModal = ref(false)
const showProductMenuModal = ref(false)
const isEditing = ref(false)
const saving = ref(false)
const searchQuery = ref('')
const sortBy = ref('name')
const selectedProduct = ref(null)

const productForm = ref({ product_code:'', product_name:'', rate:'', image:'', description:'', product_tags:[], disabled:false })

const filteredProducts = computed(()=>{
  let filtered = products.value
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    filtered = filtered.filter(p => p.product_name?.toLowerCase().includes(q) || p.product_code?.toLowerCase().includes(q) || p.description?.toLowerCase().includes(q))
  }
  filtered.sort((a,b)=>{ switch (sortBy.value){ case 'name': return (a.product_name||'').localeCompare(b.product_name||''); case 'rate': return (b.rate||0)-(a.rate||0); case 'creation': return new Date(b.creation)-new Date(a.creation); case 'code': return (a.product_code||'').localeCompare(b.product_code||''); default: return 0 } })
  return filtered
})

const productsResource = createResource({ url:'frappe.client.get_list', makeParams(){ return { doctype:'CRM Product', fields:['name','product_code','product_name','standard_rate','image','description','disabled','creation'], limit_page_length:50, order_by:'creation desc' } }, auto:true, async onSuccess(list){ const rows = await Promise.all((list||[]).map(async row=>{ try{ const full = await call('frappe.client.get',{ doctype:'CRM Product', name:row.name }); return { ...full, rate: full.standard_rate||0, product_tags: full.product_tags||[] } } catch{ return { ...row, rate: row.standard_rate||0, product_tags: [] } } })); products.value = rows } })

function refreshProducts(){ productsResource.reload() }
function addNewProduct(){ isEditing.value=false; selectedProduct.value=null; resetForm(); showAddModal.value=true }
function closeModal(){ showAddModal.value=false; showProductMenuModal.value=false; isEditing.value=false; selectedProduct.value=null; resetForm() }
function resetForm(){ productForm.value = { product_code:'', product_name:'', rate:'', image:'', description:'', product_tags:[], disabled:false } }
function editProduct(product){ isEditing.value=true; selectedProduct.value=product; productForm.value = { product_code:product.product_code, product_name:product.product_name, rate:product.rate, image:product.image||'', description:product.description||'', product_tags:(product.product_tags||[]).map(r=>({tag_name:r.tag_name, color:r.color})), disabled:product.disabled||false }; showAddModal.value=true }
function showProductMenu(product){ selectedProduct.value=product; showProductMenuModal.value=true }

async function saveProduct(){ if(!productForm.value.product_code || !productForm.value.product_name) return; saving.value=true; try{ const productData = { product_name:productForm.value.product_name, standard_rate:parseFloat(productForm.value.rate)||0, image:productForm.value.image||'', description:productForm.value.description, disabled:productForm.value.disabled }; const childRows = (productForm.value.product_tags||[]).filter(r=>r.tag_name && r.tag_name.trim().length).map(r=>({ doctype:'CRM Product Tag', parentfield:'product_tags', parenttype:'CRM Product', tag_name:r.tag_name, color:r.color||null })); if(isEditing.value && selectedProduct.value){ const doc = await call('frappe.client.get',{ doctype:'CRM Product', name:selectedProduct.value.name }); Object.assign(doc, productData); doc.product_tags = childRows; await call('frappe.client.save',{ doc }) } else { await call('frappe.client.insert',{ doc:{ doctype:'CRM Product', product_code:productForm.value.product_code, ...productData, product_tags:childRows } }) } closeModal(); refreshProducts() } catch(e){ console.error('Error saving product:', e); alert(__('Errore durante il salvataggio del prodotto.')) } finally{ saving.value=false } }

function editProductFromMenu(p){ showProductMenuModal.value=false; editProduct(p) }
async function deleteProductFromMenu(p){ showProductMenuModal.value=false; await deleteProduct(p) }
async function deleteProduct(product){ if(confirm(__('Sei sicuro di voler eliminare questo prodotto?'))){ try{ await call('frappe.client.delete',{ doctype:'CRM Product', name:product.name }); const i=products.value.findIndex(x=>x.name===product.name); if(i>-1) products.value.splice(i,1) } catch(e){ alert(__('Impossibile eliminare il prodotto.')) }}}
function addTag(){ productForm.value.product_tags.push({ tag_name:'' }) }
function removeTag(i){ productForm.value.product_tags.splice(i,1) }
async function createNewTag(value, tagRow){ if(!value) return; try{ const t=await call('frappe.client.insert',{ doc:{ doctype:'CRM Product Tag Master', tag_name:value } }); tagRow.tag_name = t.name } catch{ tagRow.tag_name = value } }
function onImageUploaded(file){ const url = file?.file_url || file?.message?.file_url || ''; if(url) productForm.value.image = url }
function removeImage(){ productForm.value.image = '' }
function getReadableTextColor(bg){ try{ const hex=bg.replace('#',''); const r=parseInt(hex.substring(0,2),16), g=parseInt(hex.substring(2,4),16), b=parseInt(hex.substring(4,6),16); const L=(0.299*r+0.587*g+0.114*b)/255; return L>0.6?'#0b1324':'#FFFFFF' }catch{ return '#0b1324' } }

usePageMeta(()=>({ title: __('Listino Prezzi') }))
</script> 