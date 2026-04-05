/**
 * API Client Service for QShieldX Backend
 * Centralized HTTP client for all backend API calls
 */

export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const API_V1 = `${API_BASE_URL}/api/v1`;

type RequestOptions = {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  headers?: Record<string, string>;
  body?: any;
  params?: Record<string, any>;
};

/**
 * Make HTTP requests to backend API
 */
async function apiRequest<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const url = new URL(endpoint.startsWith('http') ? endpoint : `${API_V1}${endpoint}`);

  // Add query parameters
  if (options.params) {
    Object.entries(options.params).forEach(([key, value]) => {
      if (value !== null && value !== undefined) {
        url.searchParams.append(key, String(value));
      }
    });
  }

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  const config: RequestInit = {
    method: options.method || 'GET',
    headers,
  };

  if (options.body) {
    config.body = JSON.stringify(options.body);
  }

  const response = await fetch(url.toString(), config);

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`API Error [${response.status}]: ${error}`);
  }

  return response.json();
}

// ════════════════════════════════════════════════════════════════════════════
// ASSETS API
// ════════════════════════════════════════════════════════════════════════════

export const assetsAPI = {
  /**
   * Get paginated list of assets
   */
  async listAssets(
    page: number = 1,
    pageSize: number = 20,
    filters?: {
      assetType?: string;
      status?: string;
      seedDomain?: string;
      minRisk?: number;
    }
  ) {
    return apiRequest('/assets', {
      method: 'GET',
      params: {
        page,
        page_size: pageSize,
        ...filters,
      },
    });
  },

  /**
   * Get single asset by ID
   */
  async getAsset(assetId: string) {
    return apiRequest(`/assets/${assetId}`, { method: 'GET' });
  },

  /**
   * Seed domains ingestion
   */
  async seedDomains(domains: string[], organization?: string, autoScan: boolean = true) {
    return apiRequest('/assets/seed-domains', {
      method: 'POST',
      body: {
        domains,
        organization,
        auto_scan: autoScan,
      },
    });
  },

  /**
   * Trigger on-demand scan for specific asset
   */
  async triggerScan(assetId: string, scanTypes: string[] = ['tls'], priority: number = 5) {
    return apiRequest(`/assets/${assetId}/scan`, {
      method: 'POST',
      body: {
        scan_types: scanTypes,
        priority,
      },
    });
  },

  /**
   * Trigger bulk scan across multiple assets
   */
  async bulkScan(
    assetIds?: string[],
    scanTypes: string[] = ['tls'],
    filters?: {
      filterByStatus?: string[];
      filterByType?: string[];
      maxAssets?: number;
    }
  ) {
    return apiRequest('/assets/bulk-scan', {
      method: 'POST',
      body: {
        asset_ids: assetIds,
        scan_types: scanTypes,
        ...filters,
      },
    });
  },

  /**
   * Delete/exclude an asset
   */
  async deleteAsset(assetId: string) {
    return apiRequest(`/assets/${assetId}`, { method: 'DELETE' });
  },
};

// ════════════════════════════════════════════════════════════════════════════
// CBOM API
// ════════════════════════════════════════════════════════════════════════════

export const cbomAPI = {
  /**
   * List CBOM records with optional filtering
   */
  async listRecords(filters?: {
    assetId?: string;
    category?: string;
    pqcStatus?: string;
  }) {
    return apiRequest('/cbom/', {
      method: 'GET',
      params: filters,
    });
  },

  /**
   * Get full CBOM for specific asset
   */
  async getAssetCBOM(assetId: string) {
    return apiRequest(`/cbom/${assetId}`, { method: 'GET' });
  },
};

// ════════════════════════════════════════════════════════════════════════════
// COMPLIANCE API
// ════════════════════════════════════════════════════════════════════════════

export const complianceAPI = {
  /**
   * Label single asset with PQC compliance status
   */
  async labelAsset(algorithms: (string | Record<string, any>)[], assetId?: string, host?: string) {
    return apiRequest('/compliance/label', {
      method: 'POST',
      body: {
        algorithms,
        asset_id: assetId,
        host,
      },
    });
  },

  /**
   * Batch label multiple assets
   */
  async labelBatch(assets: Array<{ algorithms: (string | Record<string, any>)[], assetId?: string, host?: string }>) {
    return apiRequest('/compliance/label/batch', {
      method: 'POST',
      body: {
        assets: assets.map(a => ({
          algorithms: a.algorithms,
          asset_id: a.assetId,
          host: a.host,
        })),
      },
    });
  },

  /**
   * Generate remediation playbooks
   */
  async generatePlaybook(labelResult: any) {
    return apiRequest('/compliance/playbook/generate', {
      method: 'POST',
      body: { label_result: labelResult },
    });
  },

  /**
   * Get playbook by ID
   */
  async getPlaybook(playbookId: string) {
    return apiRequest(`/compliance/playbook/${playbookId}`, { method: 'GET' });
  },

  /**
   * Request approval for critical playbook
   */
  async requestApproval(playbookId: string) {
    return apiRequest(`/compliance/approval/${playbookId}/request`, { method: 'POST' });
  },

  /**
   * Check approval status
   */
  async checkApprovalStatus(approvalId: string) {
    return apiRequest(`/compliance/approval/${approvalId}`, { method: 'GET' });
  },
};

// ════════════════════════════════════════════════════════════════════════════
// TOPOLOGY API
// ════════════════════════════════════════════════════════════════════════════

export const topologyAPI = {
  /**
   * Get full network topology graph for visualization
   */
  async getTopology() {
    return apiRequest('/topology/', { method: 'GET' });
  },

  /**
   * Get attack paths from asset to sensitive targets
   */
  async getAttackPaths(assetId: string, maxHops: number = 5) {
    return apiRequest(`/topology/attack-paths/${assetId}`, {
      method: 'GET',
      params: { max_hops: maxHops },
    });
  },
};

// ════════════════════════════════════════════════════════════════════════════
// DEV/SIMULATION API
// ════════════════════════════════════════════════════════════════════════════

export const devAPI = {
  /**
   * Trigger simulated scan
   */
  async simulateScan() {
    return apiRequest('/dev/simulate-scan', { method: 'POST' });
  },

  /**
   * Get forecast data
   */
  async getForecast() {
    return apiRequest('/dev/forecast', { method: 'GET' });
  },
};

// ════════════════════════════════════════════════════════════════════════════
// WEBSOCKET API
// ════════════════════════════════════════════════════════════════════════════

export class ComplianceWebSocket {
  private ws: WebSocket | null = null;
  private url: string;
  private messageHandlers: ((msg: any) => void)[] = [];

  constructor() {
    const wsProtocol = API_BASE_URL.startsWith('https') ? 'wss' : 'ws';
    const wsHost = API_BASE_URL.replace('http://', '').replace('https://', '');
    this.url = `${wsProtocol}://${wsHost}/api/v1/compliance/ws/alerts`;
  }

  /**
   * Connect to WebSocket and listen for alerts
   */
  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(this.url);

        this.ws.onopen = () => {
          console.log('[ws] Connected to compliance alerts stream');
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data);
            this.messageHandlers.forEach(handler => handler(message));
          } catch (e) {
            console.error('[ws] Error parsing message:', e);
          }
        };

        this.ws.onerror = (error) => {
          console.error('[ws] WebSocket error:', error);
          reject(error);
        };

        this.ws.onclose = () => {
          console.log('[ws] Disconnected from compliance alerts stream');
        };
      } catch (error) {
        reject(error);
      }
    });
  }

  /**
   * Register handler for incoming messages
   */
  onMessage(handler: (msg: any) => void): () => void {
    this.messageHandlers.push(handler);
    // Return unsubscribe function
    return () => {
      this.messageHandlers = this.messageHandlers.filter(h => h !== handler);
    };
  }

  /**
   * Send message to WebSocket
   */
  send(data: any): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }

  /**
   * Disconnect from WebSocket
   */
  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

export default {
  assetsAPI,
  cbomAPI,
  complianceAPI,
  topologyAPI,
  devAPI,
  ComplianceWebSocket,
};
