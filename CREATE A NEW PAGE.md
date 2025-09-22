# CREATE A NEW PAGE

This guide explains how to add a custom page to the CRM sidebar navigation. Follow these steps to create a new page and make it accessible through the sidebar.

## Recent Example: Listino Prodotti

The "Listino Prodotti" (Product Catalog) page was recently created as an example of a custom page that manages CRM products with an intuitive card-based interface. This page demonstrates:

- Product management with visual cards
- Integration with CRM Product doctype
- Italian localization
- CRUD operations (Create, Read, Update, Delete)
- Search and filtering functionality

## Prerequisites

- Basic knowledge of Vue.js
- Understanding of the CRM project structure
- Access to the frontend source code

## Step-by-Step Guide

### 1. Create the Page Component

Create a new Vue component in the `frontend/src/pages/` directory. Use the following template as a starting point:

```vue
<template>
  <div class="flex flex-col h-full overflow-hidden">
    <LayoutHeader>
      <template #left-header>
        <ViewBreadcrumbs routeName="YourPageName" />
      </template>
      <template #right-header>
        <Button
          :label="__('Refresh')"
          :iconLeft="LucideRefreshCcw"
          @click="refreshData"
        />
        <Button
          variant="solid"
          :label="__('Add Item')"
          :iconLeft="LucidePlus"
          @click="showAddModal = true"
        />
      </template>
    </LayoutHeader>

    <div class="p-5 flex-1 overflow-y-auto">
      <div class="mb-6">
        <h1 class="text-2xl font-semibold text-ink-gray-8 mb-2">
          {{ __('Your Page Title') }}
        </h1>
        <p class="text-ink-gray-6">
          {{ __('Your page description goes here.') }}
        </p>
      </div>

      <!-- Your page content goes here -->
      <div class="bg-white rounded-lg border border-gray-200">
        <div class="p-4 border-b border-gray-200">
          <h2 class="text-lg font-medium text-ink-gray-8">{{ __('Your Content') }}</h2>
        </div>
        <div class="p-4">
          <!-- Add your content here -->
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import LucideRefreshCcw from '~icons/lucide/refresh-ccw'
import LucidePlus from '~icons/lucide/plus'
import { Button } from 'frappe-ui'
import { ref } from 'vue'
import { usePageMeta } from 'frappe-ui'

// Your component logic goes here
const showAddModal = ref(false)

function refreshData() {
  // Your refresh logic
}

usePageMeta(() => {
  return { title: __('Your Page Title') }
})
</script>
```

**File Location:** `frontend/src/pages/YourPageName.vue`

### 2. Add Route Configuration

Add a new route to the router configuration in `frontend/src/router.js`:

```javascript
{
  path: '/your-page-path',
  name: 'YourPageName',
  component: () => import('@/pages/YourPageName.vue'),
},
```

**Important Notes:**
- Place the new route before the catch-all route (`/:invalidpath`)
- Use kebab-case for the path (e.g., `/your-page-path`)
- Use PascalCase for the component name (e.g., `YourPageName`)

### 3. Add to Desktop Sidebar

Update the `frontend/src/components/Layouts/AppSidebar.vue` file:

#### 3.1 Import Required Icon

Add your icon import at the top of the script section:

```javascript
import YourIcon from '@/components/Icons/YourIcon.vue'
```

#### 3.2 Add to Links Array

Add your page to the `links` array:

```javascript
const links = [
  // ... existing links
  {
    label: 'Your Page Label',
    icon: YourIcon,
    to: 'YourPageName',
  },
]
```

#### 3.3 Update getIcon Function

Add a case for your page in the `getIcon` function:

```javascript
function getIcon(routeName, icon) {
  if (icon) return h('div', { class: 'size-auto' }, icon)

  switch (routeName) {
    // ... existing cases
    case 'YourPageName':
      return YourIcon
    default:
      return PinIcon
  }
}
```

### 4. Add to Mobile Sidebar

Update the `frontend/src/components/Mobile/MobileSidebar.vue` file:

#### 4.1 Import Required Icon

```javascript
import YourIcon from '@/components/Icons/YourIcon.vue'
```

#### 4.2 Add to Links Array

```javascript
const links = [
  // ... existing links
  {
    label: 'Your Page Label',
    icon: YourIcon,
    to: 'YourPageName',
  },
]
```

#### 4.3 Update getIcon Function

```javascript
function getIcon(routeName, icon) {
  if (icon) return h('div', { class: 'size-auto' }, icon)

  switch (routeName) {
    // ... existing cases
    case 'YourPageName':
      return YourIcon
    default:
      return PinIcon
  }
}
```

### 5. Create Custom Icon (Optional)

If you need a custom icon, create it in `frontend/src/components/Icons/YourIcon.vue`:

```vue
<template>
  <svg
    class="h-4 w-4"
    fill="none"
    stroke="currentColor"
    viewBox="0 0 24 24"
    xmlns="http://www.w3.org/2000/svg"
  >
    <!-- Your SVG path here -->
    <path
      stroke-linecap="round"
      stroke-linejoin="round"
      stroke-width="2"
      d="M12 6v6m0 0v6m0-6h6m-6 0H6"
    />
  </svg>
</template>
```

## Example Implementation

Here's a complete example of adding a "Listino Prodotti" page:

### 1. Page Component (`frontend/src/pages/Test.vue`)
```vue
<template>
  <div class="flex flex-col h-full overflow-hidden">
    <LayoutHeader>
      <template #left-header>
        <ViewBreadcrumbs routeName="Listino Prodotti" />
      </template>
      <template #right-header>
        <Button :label="__('Aggiorna')" @click="refreshProducts" />
        <Button :label="__('Aggiungi Prodotto')" @click="showAddModal = true" />
      </template>
    </LayoutHeader>

    <div class="p-5 flex-1 overflow-y-auto">
      <h1 class="text-2xl font-semibold text-ink-gray-8 mb-2">
        {{ __('Listino Prodotti') }}
      </h1>
      <p class="text-ink-gray-6">
        {{ __('Gestisci il catalogo prodotti con prezzi e quantità.') }}
      </p>
      
      <!-- Product cards grid -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        <div v-for="product in products" :key="product.name" class="bg-white rounded-lg border p-4">
          <div class="flex items-center gap-3 mb-3">
            <div class="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
              <LucidePackage class="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <h3 class="font-medium">{{ product.product_name }}</h3>
              <p class="text-sm text-gray-600">{{ product.product_code }}</p>
            </div>
          </div>
          <div class="space-y-2">
            <div class="flex justify-between">
              <span class="text-sm">{{ __('Prezzo:') }}</span>
              <span class="font-semibold">€{{ product.rate || '0.00' }}</span>
            </div>
            <div class="flex justify-between border-t pt-2">
              <span class="text-sm font-medium">{{ __('Totale:') }}</span>
              <span class="font-bold text-green-600">€{{ product.amount || '0.00' }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import LucidePackage from '~icons/lucide/package'
import { Button, createResource } from 'frappe-ui'
import { ref } from 'vue'
import { usePageMeta } from 'frappe-ui'

const products = ref([])

const productsResource = createResource({
  url: 'frappe.client.get_list',
  makeParams() {
    return {
      doctype: 'CRM Product',
      fields: ['name', 'product_code', 'product_name', 'standard_rate', 'image', 'description'],
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

function refreshProducts() {
  productsResource.reload()
}

usePageMeta(() => {
  return { title: __('Listino Prodotti') }
})
</script>
```

### 2. Router Configuration (`frontend/src/router.js`)
```javascript
{
  path: '/listino-prodotti',
  name: 'Listino Prodotti',
  component: () => import('@/pages/Test.vue'),
},
```

### 3. Desktop Sidebar (`frontend/src/components/Layouts/AppSidebar.vue`)
```javascript
// Import
import SquareAsterisk from '@/components/Icons/SquareAsterisk.vue'

// Add to links array
{
  label: 'Listino Prodotti',
  icon: SquareAsterisk,
  to: 'Listino Prodotti',
},

// Add to getIcon function
case 'Listino Prodotti':
  return SquareAsterisk
```

### 4. Mobile Sidebar (`frontend/src/components/Mobile/MobileSidebar.vue`)
```javascript
// Import
import SquareAsterisk from '@/components/Icons/SquareAsterisk.vue'

// Add to links array
{
  label: 'Listino Prodotti',
  icon: SquareAsterisk,
  to: 'Listino Prodotti',
},

// Add to getIcon function
case 'Listino Prodotti':
  return SquareAsterisk
```

## Best Practices

1. **Consistent Naming**: Use consistent naming conventions across all files
2. **Internationalization**: Use the `__()` function for all user-facing text
3. **Responsive Design**: Ensure your page works on both desktop and mobile
4. **Error Handling**: Implement proper error handling for data operations
5. **Loading States**: Show loading indicators for async operations
6. **Accessibility**: Use semantic HTML and proper ARIA labels

## Troubleshooting

### Common Issues

1. **Page Not Found**: Ensure the route is added before the catch-all route
2. **Icon Not Showing**: Check that the icon is properly imported and added to the getIcon function
3. **Mobile Not Working**: Make sure both desktop and mobile sidebars are updated
4. **Translation Issues**: Use the `__()` function for all text that should be translatable

### Testing

1. Test the page on both desktop and mobile views
2. Verify that the sidebar link works correctly
3. Check that the page loads without errors
4. Ensure proper navigation and breadcrumbs

## Conclusion

Following this guide will help you successfully add custom pages to the CRM sidebar. Remember to maintain consistency with the existing codebase and follow the established patterns for the best results.
