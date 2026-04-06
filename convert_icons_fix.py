import os
import re

mapping = {
    'mdi:face-recognition': 'camera',
    'mdi:logout': 'log-out',
    'mdi:face-shimmer': 'sparkles',
    'mdi:loading': 'loader-2',
    'mdi:bank-outline': 'landmark',
    'mdi:cash-minus': 'arrow-down-to-line',
    'mdi:cash-plus': 'arrow-up-from-line',
    'mdi:swap-vertical': 'arrow-up-down',
    'mdi:arrow-down-left': 'arrow-down-left',
    'mdi:arrow-up-right': 'arrow-up-right',
    'mdi:history': 'history',
    'mdi:playlist-remove': 'list-x',
    'mdi:power': 'power',
    'mdi:arrow-left': 'arrow-left',
    'mdi:check-bold': 'check-circle',
    'mdi:shield-alert': 'shield-alert',
    'mdi:credit-card': 'credit-card',
    'mdi:shield-check': 'shield-check',
    'mdi:block-helper': 'ban',
    'mdi:check-decagram': 'badge-check',
    'mdi:account-outline': 'user',
    'mdi:lock-outline': 'lock',
    'mdi:shield-key-outline': 'shield-key',
    'mdi:account-group': 'users',
    'mdi:shield-alert-outline': 'shield-alert',
    'mdi:face-outline': 'user-round',
    'mdi:camera-sync-outline': 'refresh-cw',
    'mdi:bank-off': 'landmark',
    'mdi:account-plus': 'user-plus',
    'mdi:refresh': 'rotate-cw',
    'mdi:account-plus-outline': 'user-plus',
    'mdi:credit-card-chip-outline': 'credit-card',
    'mdi:account-badge-outline': 'id-card',
    'mdi:chevron-right': 'chevron-right',
    'mdi:camera-plus': 'camera',
    'mdi:alert-circle': 'alert-circle',
    'mdi:face-shimmer': 'sparkles',
}

def convert_content(content):
    # Match both <span class="..." data-icon="..."></span> AND <i data-lucide="..."></i>
    # Since I already ran it once, some are now <i data-lucide="circle-help" class="w-5 h-5"></i>
    def replace_bad_lucide(match):
        icon_name = match.group(1)
        # Try to find original if it's already circle-help
        return match.group(0) # This is too hard to recover

    # Let's just fix the ones that are currently <i data-lucide="circle-help" ...>
    # Actually, I'll just re-write the templates correctly.
    return content

# I'll just manually fix the templates one by one in blocks to ensure quality.
