/**
 * Configuration context for React app
 * Provides settings and feature toggles to all components
 */

import {
  createContext,
  ReactNode,
  useContext,
  useEffect,
  useState,
} from 'react';
import { configManager, LensConfig } from './configManager';

interface ConfigContextType {
  config: LensConfig | null;
  isLoading: boolean;
  error: string | null;
  isFeatureEnabled: (featureName: string) => boolean;
  isToolEnabled: (toolName: string) => boolean;
  refreshConfig: () => Promise<void>;
  getConfig: (path?: string) => any;
}

const ConfigContext = createContext<ConfigContextType | undefined>(undefined);

export function ConfigProvider({ children }: { children: ReactNode }) {
  const [config, setConfig] = useState<LensConfig | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refreshConfig = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const loadedConfig = await configManager.loadConfig();
      setConfig(loadedConfig);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMsg);
      console.error('Failed to load config:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    refreshConfig();
  }, []);

  const isFeatureEnabled = (featureName: string): boolean => {
    return config?.features[featureName]?.enabled ?? false;
  };

  const isToolEnabled = (toolName: string): boolean => {
    return config?.tools[toolName]?.enabled ?? false;
  };

  const getConfigValue = (path?: string): any => {
    if (!path) return config;
    // Simple path resolution: e.g., "tools.anvil.timeout"
    const parts = path.split('.');
    let value: any = config;
    for (const part of parts) {
      if (value && typeof value === 'object' && part in value) {
        value = value[part];
      } else {
        return undefined;
      }
    }
    return value;
  };

  return (
    <ConfigContext.Provider
      value={{
        config,
        isLoading,
        error,
        isFeatureEnabled,
        isToolEnabled,
        refreshConfig,
        getConfig: getConfigValue,
      }}
    >
      {children}
    </ConfigContext.Provider>
  );
}

export function useConfig(): ConfigContextType {
  const context = useContext(ConfigContext);
  if (context === undefined) {
    throw new Error('useConfig must be used within a ConfigProvider');
  }
  return context;
}
