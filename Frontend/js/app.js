const mainContent = document.querySelector(".main-content");
const pageTitle = document.querySelector(".topbar h1");
const pageDescription = document.querySelector(".topbar p");
const menuItems = document.querySelectorAll(".sidebar nav a");

const API = "http://127.0.0.1:5000/api";

const pages = {
    Dashboard: "Welcome back! Here's your business overview.",
    Customers: "Manage your customers.",
    Subscriptions: "Manage customer subscriptions.",
    Plans: "Manage your subscription plans.",
    Invoices: "View and manage invoices.",
    Payments: "Track customer payments.",
    Reports: "View business reports."
};

const sampleSubscriptions = [
    { customer: "Ananya Thomas", plan: "Premium", amount: "₹2,999", status: "Active" },
    { customer: "Rahul Kumar", plan: "Basic", amount: "₹999", status: "Active" },
    { customer: "Meera Nair", plan: "Business", amount: "₹4,999", status: "Pending" },
    { customer: "Arjun Das", plan: "Premium", amount: "₹2,999", status: "Active" }
];

function renderSampleSubscriptions() {
    const table = document.getElementById("subscriptionTable");
    if (!table) return;

    table.innerHTML = sampleSubscriptions.map(item => `
        <tr>
            <td>${item.customer}</td>
            <td>${item.plan}</td>
            <td>${item.amount}</td>
            <td>
                <span class="status ${item.status === "Pending" ? "pending" : ""}">
                    ${item.status}
                </span>
            </td>
        </tr>
    `).join("");
}

// --------------------------------------------------
// PAGE NAVIGATION
// --------------------------------------------------

function showPage(pageName) {
    if (!pages[pageName]) return;

    pageTitle.textContent = pageName;
    pageDescription.textContent = pages[pageName];

    mainContent.querySelectorAll(".page-content").forEach(el => el.remove());

    mainContent.querySelectorAll(".stats-grid, .content-grid").forEach(el => {
        el.style.display = pageName === "Dashboard" ? "" : "none";
    });

    if (pageName === "Dashboard") {
        renderSampleSubscriptions();
    } else {
        const section = document.createElement("section");
        section.className = "page-content";

        if (pageName === "Subscriptions") {
            section.innerHTML = `
                <div class="panel">
                    <div class="panel-heading">
                        <h3>Subscription Management</h3>
                        <button id="createSubscriptionBtn" class="primary-btn">
                            + Create Subscription
                        </button>
                    </div>

                    <div id="subscriptionFormContainer"></div>

                    <div class="table-wrapper">
                        <table>
                            <thead>
                                <tr>
                                    <th>ID</th>
                                    <th>Customer ID</th>
                                    <th>Plan</th>
                                    <th>Quantity</th>
                                    <th>Total Price</th>
                                    <th>Status</th>
                                    <th>Start Date</th>
                                </tr>
                            </thead>
                            <tbody id="subscriptionList">
                                <tr><td colspan="7">Loading subscriptions...</td></tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            `;
        } else if (pageName === "Plans") {
            section.innerHTML = `
                <div class="panel">
                    <div class="panel-heading">
                        <h3>Subscription Plans</h3>
                        <button id="createPlanBtn" class="primary-btn">
                            + Create Plan
                        </button>
                    </div>

                    <div id="planFormContainer"></div>

                    <div class="table-wrapper">
                        <table>
                            <thead>
                                <tr>
                                    <th>ID</th>
                                    <th>Plan Name</th>
                                    <th>Variant ID</th>
                                    <th>Billing Interval</th>
                                    <th>Price</th>
                                    <th>Trial Days</th>
                                    <th>Status</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody id="planList">
                                <tr><td colspan="8">Loading plans...</td></tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            `;
        } else {
            section.innerHTML = `
                <div class="panel">
                    <h3>${pageName}</h3>
                    <p>${pages[pageName]}</p>
                    <p>Backend integration pending.</p>
                </div>
            `;
        }

        mainContent.insertBefore(section, mainContent.querySelector(".footer"));

        if (pageName === "Subscriptions") {
            document.getElementById("createSubscriptionBtn")
                .addEventListener("click", showSubscriptionForm);

            loadSubscriptions();
        }

        if (pageName === "Plans") {
            document.getElementById("createPlanBtn")
                .addEventListener("click", showPlanForm);

            loadPlans();
        }
    }

    menuItems.forEach(item => {
        item.classList.toggle("active", item.dataset.page === pageName);
    });
}

menuItems.forEach(item => {
    item.addEventListener("click", event => {
        event.preventDefault();
        showPage(item.dataset.page);
    });
});

// --------------------------------------------------
// SUBSCRIPTIONS
// --------------------------------------------------

async function loadSubscriptions() {
    const table = document.getElementById("subscriptionList");

    try {
        const response = await fetch(`${API}/subscriptions/`);
        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || "Could not load subscriptions");
        }

        if (!result.subscriptions || result.subscriptions.length === 0) {
            table.innerHTML = `
                <tr><td colspan="7">No subscriptions found. Create your first subscription.</td></tr>
            `;
            return;
        }

        table.innerHTML = result.subscriptions.map(sub => `
            <tr>
                <td>${sub.id}</td>
                <td>${sub.customer_id}</td>
                <td>${sub.plan_name}</td>
                <td>${sub.quantity}</td>
                <td>₹${Number(sub.total_price).toLocaleString("en-IN")}</td>
                <td><span class="status">${sub.status}</span></td>
                <td>${sub.start_date}</td>
            </tr>
        `).join("");

    } catch (error) {
        table.innerHTML = `<tr><td colspan="7">${error.message}</td></tr>`;
        console.error(error);
    }
}

async function showSubscriptionForm() {
    const container = document.getElementById("subscriptionFormContainer");

    container.innerHTML = `
        <div class="subscription-form">
            <h3>Create New Subscription</h3>

            <form id="subscriptionForm">
                <label>Customer ID</label>
                <input type="number" id="customerId" min="1" required>

                <label>Subscription Plan</label>
                <select id="planId" required>
                    <option value="">Loading plans...</option>
                </select>

                <label>Quantity</label>
                <input type="number" id="quantity" value="1" min="1" required>

                <label>Start Date</label>
                <input type="date" id="startDate" required>

                <button type="submit" class="primary-btn">
                    Create Subscription
                </button>

                <button type="button" id="cancelFormBtn">Cancel</button>

                <p id="formMessage"></p>
            </form>
        </div>
    `;

    const planSelect = document.getElementById("planId");

    try {
        const response = await fetch(`${API}/subscription-plans/`);
        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || "Unable to load plans");
        }

        planSelect.innerHTML = `<option value="">Select a plan</option>`;

        result.plans.filter(plan => plan.is_active).forEach(plan => {
            const option = document.createElement("option");
            option.value = plan.id;
            option.textContent =
                `${plan.plan_name} - ₹${Number(plan.price).toLocaleString("en-IN")} (${plan.billing_interval})`;
            planSelect.appendChild(option);
        });

    } catch (error) {
        planSelect.innerHTML = `<option value="">Unable to load plans</option>`;
    }

    document.getElementById("startDate").value =
        new Date().toISOString().split("T")[0];

    document.getElementById("cancelFormBtn").addEventListener("click", () => {
        container.innerHTML = "";
    });

    document.getElementById("subscriptionForm")
        .addEventListener("submit", createSubscription);
}

async function createSubscription(event) {
    event.preventDefault();

    const message = document.getElementById("formMessage");

    const data = {
        customer_id: Number(document.getElementById("customerId").value),
        plan_id: Number(document.getElementById("planId").value),
        quantity: Number(document.getElementById("quantity").value),
        start_date: document.getElementById("startDate").value
    };

    message.textContent = "Creating subscription...";

    try {
        const response = await fetch(`${API}/subscriptions/`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || result.message || "Subscription creation failed");
        }

        alert("Subscription created successfully!");

        document.getElementById("subscriptionFormContainer").innerHTML = "";
        await loadSubscriptions();

    } catch (error) {
        message.textContent = error.message;
        message.style.color = "red";
    }
}

// --------------------------------------------------
// SUBSCRIPTION PLANS
// --------------------------------------------------

async function loadPlans() {
    const table = document.getElementById("planList");

    try {
        const response = await fetch(`${API}/subscription-plans/`);
        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || "Could not load plans");
        }

        if (!result.plans || result.plans.length === 0) {
            table.innerHTML = `
                <tr><td colspan="8">No plans found. Create your first plan.</td></tr>
            `;
            return;
        }

        table.innerHTML = result.plans.map(plan => `
            <tr>
                <td>${plan.id}</td>
                <td>${plan.plan_name}</td>
                <td>${plan.variant_id}</td>
                <td>${plan.billing_interval.replace("_", " ")}</td>
                <td>₹${Number(plan.price).toLocaleString("en-IN")}</td>
                <td>${plan.trial_days}</td>
                <td>
                    <span class="status ${plan.is_active ? "" : "pending"}">
                        ${plan.is_active ? "Active" : "Inactive"}
                    </span>
                </td>
                <td>
                    <button class="action-btn"
                        onclick="togglePlanStatus(${plan.id}, ${plan.is_active})">
                        ${plan.is_active ? "Deactivate" : "Activate"}
                    </button>
                    <button class="action-btn delete-btn"
                        onclick="deletePlan(${plan.id})">
                        Delete
                    </button>
                </td>
            </tr>
        `).join("");

    } catch (error) {
        table.innerHTML = `<tr><td colspan="8">${error.message}</td></tr>`;
        console.error(error);
    }
}

// CREATE PLAN FORM

async function showPlanForm() {
    const container = document.getElementById("planFormContainer");

    container.innerHTML = `
        <div class="subscription-form">
            <h3>Create New Subscription Plan</h3>

            <form id="planForm">
                <label>Product Variant</label>
                <select id="variantId" required>
                    <option value="">Loading variants...</option>
                </select>

                <label>Plan Name</label>
                <input type="text" id="planName" placeholder="Example: Basic Monthly" required>

                <label>Billing Interval</label>
                <select id="billingInterval" required>
                    <option value="monthly">Monthly</option>
                    <option value="quarterly">Quarterly</option>
                    <option value="half_yearly">Half Yearly</option>
                    <option value="yearly">Yearly</option>
                </select>

                <label>Price (₹)</label>
                <input type="number" id="planPrice" min="0.01" step="0.01" required>

                <label>Trial Days</label>
                <input type="number" id="trialDays" min="0" value="0">

                <label>Description</label>
                <input type="text" id="planDescription" placeholder="Plan description">

                <button type="submit" class="primary-btn">Save Plan</button>
                <button type="button" id="cancelPlanBtn">Cancel</button>

                <p id="planFormMessage"></p>
            </form>
        </div>
    `;

    const variantSelect = document.getElementById("variantId");

    try {
        const response = await fetch(`${API}/products/1/variants`);
        const variants = await response.json();

        if (!response.ok) {
            throw new Error("Unable to load product variants");
        }

        variantSelect.innerHTML = `<option value="">Select a variant</option>`;

        variants.filter(variant => variant.is_active).forEach(variant => {
            const option = document.createElement("option");
            option.value = variant.id;
            option.textContent =
                `${variant.variant_name} - ₹${Number(variant.price).toLocaleString("en-IN")}`;
            variantSelect.appendChild(option);
        });

    } catch (error) {
        variantSelect.innerHTML = `<option value="">Unable to load variants</option>`;
        console.error(error);
    }

    document.getElementById("cancelPlanBtn").addEventListener("click", () => {
        container.innerHTML = "";
    });

    document.getElementById("planForm").addEventListener("submit", createPlan);
}

// SAVE PLAN

async function createPlan(event) {
    event.preventDefault();

    const message = document.getElementById("planFormMessage");

    const data = {
        variant_id: Number(document.getElementById("variantId").value),
        plan_name: document.getElementById("planName").value.trim(),
        billing_interval: document.getElementById("billingInterval").value,
        price: Number(document.getElementById("planPrice").value),
        trial_days: Number(document.getElementById("trialDays").value || 0),
        description: document.getElementById("planDescription").value.trim()
    };

    message.textContent = "Saving plan...";

    try {
        const response = await fetch(`${API}/subscription-plans/`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || result.message || "Could not create plan");
        }

        alert("Subscription plan created successfully!");

        document.getElementById("planFormContainer").innerHTML = "";
        await loadPlans();

    } catch (error) {
        message.textContent = error.message;
        message.style.color = "red";
    }
}

// ACTIVATE / DEACTIVATE PLAN

async function togglePlanStatus(planId, currentStatus) {
    try {
        const response = await fetch(`${API}/subscription-plans/${planId}/status`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ is_active: !currentStatus })
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || result.message || "Could not update plan status");
        }

        await loadPlans();

    } catch (error) {
        alert(error.message);
    }
}

// DELETE PLAN

async function deletePlan(planId) {
    if (!confirm("Are you sure you want to delete this plan?")) {
        return;
    }

    try {
        const response = await fetch(`${API}/subscription-plans/${planId}`, {
            method: "DELETE"
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || result.message || "Could not delete plan");
        }

        alert("Plan deleted successfully!");
        await loadPlans();

    } catch (error) {
        alert(error.message);
    }
}

// --------------------------------------------------
// INITIALIZE APPLICATION
// --------------------------------------------------

renderSampleSubscriptions();
showPage("Dashboard");

console.log("Brightloop application initialized.");