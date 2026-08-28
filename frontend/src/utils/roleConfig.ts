/**
 * Role configuration — maps role IDs to display info and theme colors.
 */
import type { UserRole } from '../store/authStore';

export interface RoleConfig {
  id: UserRole;
  label: string;
  shortLabel: string;
  color: string;
  colorLight: string;
  colorDark: string;
  icon: string;
  homePath: string;
  description: string;
}

export const ROLE_CONFIGS: Record<UserRole, RoleConfig> = {
  citizen: {
    id: 'citizen',
    label: 'Citizen / Consumer',
    shortLabel: 'Citizen',
    color: 'var(--color-citizen)',
    colorLight: 'var(--color-citizen-light)',
    colorDark: 'var(--color-citizen-dark)',
    icon: '👤',
    homePath: '/citizen',
    description: 'Scan products, check compliance, file complaints',
  },
  field_officer: {
    id: 'field_officer',
    label: 'Field Officer / Inspector',
    shortLabel: 'Officer',
    color: 'var(--color-officer)',
    colorLight: 'var(--color-officer-light)',
    colorDark: 'var(--color-officer-dark)',
    icon: '🔍',
    homePath: '/officer',
    description: 'Inspect products, capture labels, create cases',
  },
  state_controller: {
    id: 'state_controller',
    label: 'State Controller',
    shortLabel: 'Controller',
    color: 'var(--color-controller)',
    colorLight: 'var(--color-controller-light)',
    colorDark: 'var(--color-controller-dark)',
    icon: '🏛️',
    homePath: '/controller',
    description: 'Manage state-level enforcement, approve escalations',
  },
  national_admin: {
    id: 'national_admin',
    label: 'National Admin / DoCA',
    shortLabel: 'National',
    color: 'var(--color-national)',
    colorLight: 'var(--color-national-light)',
    colorDark: 'var(--color-national-dark)',
    icon: '🇮🇳',
    homePath: '/admin',
    description: 'Cross-state analytics, policy simulation, rule publishing',
  },
  business: {
    id: 'business',
    label: 'Business Portal',
    shortLabel: 'Business',
    color: 'var(--color-business)',
    colorLight: 'var(--color-business-light)',
    colorDark: 'var(--color-business-dark)',
    icon: '🏢',
    homePath: '/business',
    description: 'Pre-market checks, compliance records, notices',
  },
  ecommerce_partner: {
    id: 'ecommerce_partner',
    label: 'E-commerce Integration',
    shortLabel: 'E-commerce',
    color: 'var(--color-ecommerce)',
    colorLight: 'var(--color-ecommerce-light)',
    colorDark: 'var(--color-ecommerce-dark)',
    icon: '🛒',
    homePath: '/ecommerce',
    description: 'Bulk upload listings, review flagged products',
  },
  rule_admin: {
    id: 'rule_admin',
    label: 'Rule Engine Admin',
    shortLabel: 'Rule Admin',
    color: 'var(--color-ruleadmin)',
    colorLight: 'var(--color-ruleadmin-light)',
    colorDark: 'var(--color-ruleadmin-dark)',
    icon: '⚖️',
    homePath: '/admin',
    description: 'Draft, simulate, and publish compliance rules',
  },
};

export const getRoleConfig = (role: UserRole): RoleConfig => {
  return ROLE_CONFIGS[role];
};

export const ALL_ROLES: UserRole[] = [
  'citizen',
  'field_officer',
  'state_controller',
  'national_admin',
  'business',
  'ecommerce_partner',
  'rule_admin',
];
