const API_BASE_URL = "http://127.0.0.1:5000/api";

async function apiRequest(endpoint) {
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`);
        const result = await response.json();

        if (!response.ok || result.status !== "success") {
            throw new Error(result.message || "API request failed");
        }

        return result.data;
    } catch (error) {
        console.error("API Error:", error.message);
        throw error;
    }
}

async function getDashboardSummary() {
    return apiRequest("/dashboard/summary");
}

async function getSubscriptions() {
    return apiRequest("/subscriptions");
}

async function getCustomers() {
    return apiRequest("/customers");
}

async function getInvoices() {
    return apiRequest("/invoices");
}

async function getPayments() {
    return apiRequest("/payments");
}