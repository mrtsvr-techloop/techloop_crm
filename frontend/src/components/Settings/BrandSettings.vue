<template>
  <div class="flex h-full flex-col gap-6 px-6 py-8 text-ink-gray-8">
    <!-- Header -->
    <div class="flex justify-between px-2 text-ink-gray-8">
      <div class="flex flex-col gap-1">
        <h2 class="flex gap-2 text-xl font-semibold leading-none h-5">
          {{ __('Brand settings') }}
        </h2>
        <p class="text-p-base text-ink-gray-6">
          {{ __('Configure your brand name, logo, and favicon') }}
        </p>
      </div>
      <div class="flex item-center space-x-2 w-3/12 justify-end">
        <Button
          :label="__('Update')"
          variant="solid"
          :disabled="!settings.isDirty"
          :loading="settings.loading"
          @click="updateSettings"
        />
      </div>
    </div>

    <!-- Fields -->
    <div class="flex flex-1 flex-col p-2 gap-4 overflow-y-auto">
      <div class="flex w-full">
        <FormControl
          type="text"
          class="w-1/2"
          size="md"
          v-model="settings.doc.brand_name"
          :label="__('Brand name')"
          :placeholder="__('Enter brand name')"
        />
      </div>

      <!-- logo -->
      <div class="flex flex-col justify-between gap-4">
        <div class="flex items-center flex-1 gap-5">
          <div
            class="flex items-center justify-center rounded border border-outline-gray-modals size-20"
          >
            <img
              v-if="settings.doc?.brand_logo"
              :src="settings.doc?.brand_logo"
              alt="Logo"
              class="size-8 rounded"
            />
            <ImageIcon v-else class="size-5 text-ink-gray-4" />
          </div>
          <div class="flex flex-1 flex-col gap-1">
            <span class="text-base font-medium">{{ __('Brand logo') }}</span>
            <span class="text-p-base text-ink-gray-6">
              {{
                __(
                  'Appears in the left sidebar. Recommended size is 32x32 px in PNG or SVG',
                )
              }}
            </span>
          </div>
          <div>
            <ImageUploader
              image_type="image/ico"
              :image_url="settings.doc?.brand_logo"
              @upload="(url) => (settings.doc.brand_logo = url)"
              @remove="() => (settings.doc.brand_logo = '')"
            />
          </div>
        </div>
      </div>

      <!-- favicon -->
      <div class="flex flex-col justify-between gap-4">
        <div class="flex items-center flex-1 gap-5">
          <div
            class="flex items-center justify-center rounded border border-outline-gray-modals size-20"
          >
            <img
              v-if="settings.doc?.favicon"
              :src="settings.doc?.favicon"
              alt="Favicon"
              class="size-8 rounded"
            />
            <ImageIcon v-else class="size-5 text-ink-gray-4" />
          </div>
          <div class="flex flex-1 flex-col gap-1">
            <span class="text-base font-medium">{{ __('Favicon') }}</span>
            <span class="text-p-base text-ink-gray-6">
              {{
                __(
                  'Appears next to the title in your browser tab. Recommended size is 32x32 px in PNG or ICO',
                )
              }}
            </span>
          </div>
          <div>
            <ImageUploader
              image_type="image/ico"
              :image_url="settings.doc?.favicon"
              @upload="(url) => (settings.doc.favicon = url)"
              @remove="() => (settings.doc.favicon = '')"
            />
          </div>
        </div>
      </div>

      <!-- Payment Info -->
      <div class="flex flex-col gap-2">
        <div class="flex flex-col gap-1">
          <span class="text-base font-medium">{{ __('Payment Information') }}</span>
          <span class="text-p-base text-ink-gray-6">
            {{
              __(
                'Enter payment information that will be included in WhatsApp messages when the order status is "Attesa Pagamento". You can include IBAN, PayPal, instructions, etc.'
              )
            }}
          </span>
        </div>
        <FormControl
          type="textarea"
          v-model="settings.doc.payment_info_text"
          :label="__('Payment Information Text')"
          :placeholder="__('Enter payment information...')"
          rows="6"
        />
      </div>

      <!-- Status Notifications -->
      <div class="flex flex-col gap-4">
        <div class="flex flex-col gap-1">
          <span class="text-base font-medium">{{ __('Status Change Notifications') }}</span>
          <span class="text-p-base text-ink-gray-6">
            {{
              __(
                'Configure WhatsApp notifications for each status change. Enable/disable notifications and customize the message for each status.'
              )
            }}
          </span>
        </div>

        <!-- Dynamic Status Fields -->
        <div
          v-for="status in leadStatuses.data"
          :key="status.name"
          class="flex flex-col gap-2 border-t border-outline-gray-modals pt-4"
        >
          <FormControl
            type="checkbox"
            v-model="settings.doc[getEnableFieldName(status.name)]"
            :label="getEnableNotificationLabel(status.name)"
          />
          <FormControl
            v-if="settings.doc[getEnableFieldName(status.name)]"
            type="textarea"
            v-model="settings.doc[getMessageFieldName(status.name)]"
            :label="getCustomMessageLabel(status.name)"
            :placeholder="__('Leave empty to use default message')"
            rows="3"
          />
        </div>
      </div>
    </div>
  </div>
</template>
<script setup>
import { computed } from 'vue'
import ImageIcon from '~icons/lucide/image'
import ImageUploader from '@/components/Controls/ImageUploader.vue'
import { FormControl } from 'frappe-ui'
import { getSettings } from '@/stores/settings'
import { showSettings } from '@/composables/settings'
import { statusesStore } from '@/stores/statuses'

const { _settings: settings, setupBrand } = getSettings()
const { leadStatuses } = statusesStore()

/**
 * Converte il nome di uno stato in uno slug valido per i nomi dei campi.
 * Es: "Awaiting Payment" -> "awaiting_payment"
 */
function slugifyStatusName(statusName) {
  return statusName
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '')
}

/**
 * Ottiene il nome del campo boolean per abilitare/disabilitare la notifica per uno stato.
 */
function getEnableFieldName(statusName) {
  return `enable_notification_${slugifyStatusName(statusName)}`
}

/**
 * Ottiene il nome del campo text per il messaggio personalizzato per uno stato.
 */
function getMessageFieldName(statusName) {
  return `custom_message_${slugifyStatusName(statusName)}`
}

/**
 * Ottiene la label tradotta per il campo "Enable notification".
 * Mostra il nome completo dello stato tradotto.
 */
function getEnableNotificationLabel(statusName) {
  const statusLabel = __(statusName)
  // Usa template literal invece di formato traduzione per evitare problemi con placeholder
  return __('Enable notification for') + ' ' + statusLabel
}

/**
 * Ottiene la label tradotta per il campo "Custom message".
 * Mostra il nome completo dello stato tradotto.
 */
function getCustomMessageLabel(statusName) {
  const statusLabel = __(statusName)
  // Usa template literal invece di formato traduzione per evitare problemi con placeholder
  return __('Custom message for') + ' ' + statusLabel
}

function updateSettings() {
  settings.save.submit(null, {
    onSuccess: () => {
      showSettings.value = false
      setupBrand()
    },
  })
}
</script>
