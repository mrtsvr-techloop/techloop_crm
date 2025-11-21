<template>
  <Dialog
    v-model="showSettings"
    :options="{ size: '5xl' }"
    @close="activeSettingsPage = ''"
    :disableOutsideClickToClose="disableSettingModalOutsideClick"
  >
    <template #body>
      <div class="flex h-[calc(100vh_-_8rem)]">
        <div class="flex flex-col p-1 w-52 shrink-0 bg-surface-gray-2">
          <h1 class="px-3 pt-3 pb-2 text-lg font-semibold text-ink-gray-8">
            {{ __('Settings') }}
          </h1>
          <div class="flex flex-col overflow-y-auto">
            <template v-for="tab in tabs" :key="tab.label">
              <div
                v-if="!tab.hideLabel && !tab.hidden"
                class="py-[7px] px-2 my-1 flex cursor-pointer gap-1.5 text-base text-ink-gray-5 transition-all duration-300 ease-in-out"
              >
                <span>{{ __(tab.label) }}</span>
              </div>
              <nav class="space-y-1 px-1">
                <SidebarLink
                  v-for="i in tab.items"
                  :key="i.label"
                  :icon="i.icon"
                  :label="__(i.label)"
                  class="w-full"
                  :class="[
                    activeTab?.label == i.label
                      ? 'bg-surface-selected shadow-sm hover:bg-surface-selected'
                      : 'hover:bg-surface-gray-3',
                    i.hidden ? 'opacity-0 h-0 overflow-hidden' : ''
                  ]"
                  @click="activeSettingsPage = i.label"
                />
              </nav>
            </template>
          </div>
        </div>
        <div class="flex flex-col flex-1 overflow-y-auto bg-surface-modal">
          <component :is="activeTab.component" v-if="activeTab" />
        </div>
      </div>
    </template>
  </Dialog>
</template>
<script setup>
import CircleDollarSignIcon from '~icons/lucide/circle-dollar-sign'
import TrendingUpDownIcon from '~icons/lucide/trending-up-down'
import SparkleIcon from '@/components/Icons/SparkleIcon.vue'
import WhatsAppIcon from '@/components/Icons/WhatsAppIcon.vue'
import ERPNextIcon from '@/components/Icons/ERPNextIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import Email2Icon from '@/components/Icons/Email2Icon.vue'
import EmailTemplateIcon from '@/components/Icons/EmailTemplateIcon.vue'
import SettingsIcon2 from '@/components/Icons/SettingsIcon2.vue'
import Users from '@/components/Settings/Users.vue'
import InviteUserPage from '@/components/Settings/InviteUserPage.vue'
import ProfileSettings from '@/components/Settings/ProfileSettings.vue'
import WhatsAppSettings from '@/components/Settings/WhatsAppSettings.vue'
import ERPNextSettings from '@/components/Settings/ERPNextSettings.vue'
import LeadSyncSourcePage from '@/components/Settings/LeadSyncing/LeadSyncSourcePage.vue'
import BrandSettings from '@/components/Settings/BrandSettings.vue'
import HomeActions from '@/components/Settings/HomeActions.vue'
import ForecastingSettings from '@/components/Settings/ForecastingSettings.vue'
import CurrencySettings from '@/components/Settings/CurrencySettings.vue'
import EmailTemplatePage from '@/components/Settings/EmailTemplate/EmailTemplatePage.vue'
import TelephonySettings from '@/components/Settings/TelephonySettings.vue'
import EmailConfig from '@/components/Settings/EmailConfig.vue'
import SidebarLink from '@/components/SidebarLink.vue'
import { usersStore } from '@/stores/users'
import {
  isWhatsappInstalled,
  showSettings,
  activeSettingsPage,
  disableSettingModalOutsideClick,
} from '@/composables/settings'
import { Dialog, Avatar } from 'frappe-ui'
import { ref, markRaw, computed, watch, h } from 'vue'
import AssignmentRulePage from './AssignmentRules/AssignmentRulePage.vue'
import SpecialFunctions from './SpecialFunctions.vue'

const { isManager, isTelephonyAgent, getUser } = usersStore()

const user = computed(() => getUser() || {})

const tabs = computed(() => {
  let _tabs = [
    {
      label: __('System Configuration'),
      items: [
        {
          label: __('Currency & Exchange Rate'),
          icon: CircleDollarSignIcon,
          component: markRaw(CurrencySettings),
        },
        {
          label: __('Brand Settings'),
          icon: SparkleIcon,
          component: markRaw(BrandSettings),
        },
      ],
      condition: () => isManager(),
    },
    {
      label: __('User Management'),
      items: [
        {
          label: __('Users'),
          icon: 'user',
          component: markRaw(Users),
          condition: () => isManager(),
        },
        {
          label: __('Invite User'),
          icon: 'user-plus',
          component: markRaw(InviteUserPage),
          condition: () => isManager(),
        },
      ],
      condition: () => isManager(),
    },
    {
      label: __('Integrations', null, 'FCRM'),
      items: [
        {
          label: __('WhatsApp'),
          icon: WhatsAppIcon,
          component: markRaw(WhatsAppSettings),
          condition: () => isWhatsappInstalled.value && isManager(),
        },
      ],
      condition: () => isManager(),
    },
    {
      label: __('System Tools'),
      items: [
        {
          label: __('Special Functions'),
          icon: 'settings',
          component: markRaw(SpecialFunctions),
          condition: () => isManager(),
          hidden: true, // Nascosto ma accessibile
        },
      ],
      condition: () => isManager(),
      hidden: true, // Nascosto ma accessibile
    },
  ]

  return _tabs.filter((tab) => {
    if (tab.condition && !tab.condition()) return false
    if (tab.items) {
      tab.items = tab.items.filter((item) => {
        if (item.condition && !item.condition()) return false
        return true
      })
    }
    return true
  })
})

const activeTab = ref(tabs.value[0].items[0])

function setActiveTab(tabName) {
  activeTab.value =
    (tabName &&
      tabs.value
        .map((tab) => tab.items)
        .flat()
        .find((tab) => tab.label === tabName)) ||
    tabs.value[0].items[0]
}

watch(activeSettingsPage, (activePage) => setActiveTab(activePage))
</script>
