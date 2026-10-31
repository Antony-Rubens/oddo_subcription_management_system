const subscriptions = [
    { customer: "Ananya Thomas", plan: "Premium", amount: "₹2,999", status: "Active" },
    { customer: "Rahul Kumar", plan: "Basic", amount: "₹999", status: "Active" },
    { customer: "Meera Nair", plan: "Business", amount: "₹4,999", status: "Pending" },
    { customer: "Arjun Das", plan: "Premium", amount: "₹2,999", status: "Active" }
];

const table = document.getElementById("subscriptionTable");

table.innerHTML = subscriptions.map(item => `
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
console.log("Dashboard JavaScript loaded successfully!");
console.log("API connection functions:", typeof getDashboardSummary);