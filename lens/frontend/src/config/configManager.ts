/**
 * Configuration loader and manager
 * Loads settings from settings.json and supports environment variable overrides
 */

export interface FeatureConfig {
  enabled: boolean;
  name: string;
  description: string;
  icon: string;
}

export interface ToolConfig {
  enabled: boolean;
  path: string;
  timeout: number;
}

export interface LensConfig {
  version: string;
  features: Record<string, FeatureConfig>;
  tools: Record<string, ToolConfig>;
  ui: {
    theme: 'light' | 'dark';
    sidebarCollapsed: boolean;
    defaultResultsPerPage: number;
  };
  output: {
    colorEnabled: boolean;
    verbosity: 'debug' | 'info' | 'warn' | 'error';
  };
}

class ConfigManager {
  private config: LensConfig | null = null;

  async loadConfig(): Promise<LensConfig> {
    if (this.config) {
      return this.config;
    }

    try {
      const response = await fetch('/config/settings.json');
      if (!response.ok) {
        throw new Error(`Failed to load config: ${response.statusText}`);
      }
      this.config = await response.json();

      // Apply environment variable overrides
      this.applyEnvOverrides();

      return this.config;
    } catch (error) {
      console.error('Error loading configuration:', error);
      // Return minimal default config
      return this.getDefaultConfig();
    }
  }

  private applyEnvOverrides(): void {
    if (!this.config) return;

    // Check for feature toggles via env vars: LENS_FEATURE_<FEATURENAME>=true/false
    Object.keys(this.config.features).forEach((feature) => {
      const envKey = `VITE_LENS_FEATURE_${feature.toUpperCase()}`;
      const envValue = import.meta.env[envKey];
      if (envValue !== undefined) {
        this.config!.features[feature].enabled = envValue === 'true';
      }
    });

    // Check for tool paths via env vars: LENS_TOOL_<TOOLNAME>_PATH
    Object.keys(this.config.tools).forEach((tool) => {
      const pathEnvKey = `VITE_LENS_TOOL_${tool.toUpperCase()}_PATH`;
      const enabledEnvKey = `VITE_LENS_TOOL_${tool.toUpperCase()}_ENABLED`;

      const pathValue = import.meta.env[pathEnvKey];
      const enabledValue = import.meta.env[enabledEnvKey];

      if (pathValue) {
        this.config!.tools[tool].path = pathValue;
      }
      if (enabledValue !== undefined) {
        this.config!.tools[tool].enabled = enabledValue === 'true';
      }
    });
  }

  private getDefaultConfig(): LensConfig {
    return {
      version: '1.0',
      features: {
        localInspection: {
          enabled: true,
          name: 'Local Inspection',
          description: 'Analyze code quality, coverage, and style issues',
          icon: 'FileText',
        },
        localTests: {
          enabled: true,
          name: 'Local Tests',
          description: 'Execute and analyze test suites',
          icon: 'CheckCircle',
        },
        localBuild: {
          enabled: false,
          name: 'Local Build',
          description: 'Configure and compile projects',
          icon: 'Hammer',
        },
        localExecution: {
          enabled: false,
          name: 'Local Execution',
          description: 'Run and monitor command execution',
          icon: 'Play',
        },
        ciInspection: {
          enabled: true,
          name: 'CI Inspection',
          description: 'Analyze CI/CD workflow execution',
          icon: 'Activity',
        },
      },
      tools: {
        anvil: { enabled: true, path: './anvil', timeout: 30000 },
        forge: { enabled: false, path: './forge', timeout: 60000 },
        scout: { enabled: true, path: './scout', timeout: 30000 },
        verdict: { enabled: true, path: './verdict', timeout: 60000 },
        gaze: { enabled: false, path: './gaze', timeout: 30000 },
      },
      ui: {
        theme: 'light',
        sidebarCollapsed: false,
        defaultResultsPerPage: 50,
      },
      output: {
        colorEnabled: true,
        verbosity: 'info',
      },
    };
  }

  getConfig(): LensConfig {
    if (!this.config) {
      return this.getDefaultConfig();
    }
    return this.config;
  }

  isFeatureEnabled(featureName: string): boolean {
    const config = this.getConfig();
    return config.features[featureName]?.enabled ?? false;
  }

  isToolEnabled(toolName: string): boolean {
    const config = this.getConfig();
    return config.tools[toolName]?.enabled ?? false;
  }

  getFeature(featureName: string): FeatureConfig | null {
    const config = this.getConfig();
    return config.features[featureName] ?? null;
  }

  getEnabledFeatures(): FeatureConfig[] {
    const config = this.getConfig();
    return Object.values(config.features).filter((f) => f.enabled);
  }
}

export const configManager = new ConfigManager();
