// grant-report.js (shared for admin & user pages)
document.addEventListener("DOMContentLoaded", function () {
  const grantSelect = document.querySelector("#grant_select");
  if (!grantSelect) return;

  function clearReport() {
    document.querySelectorAll(".info-name, .info-dept, .info-title, .info-grantno")
      .forEach(el => { if (el) el.textContent = ""; });

    document.querySelectorAll(".budget-year1, .budget-year2, .budget-total")
      .forEach(el => { if (el) el.textContent = ""; });

    const budgetTbody = document.querySelector("#budget-table tbody");
    if (budgetTbody) budgetTbody.innerHTML = "";

    const expTbody = document.querySelector("#expenditure-table tbody");
    if (expTbody) expTbody.innerHTML = "";
  }

  grantSelect.addEventListener("change", function () {
    const grantNo = this.value;
    if (!grantNo) {
      clearReport();
      return;
    }

    fetch(`/get-seed-grant-details/?grant_no=${encodeURIComponent(grantNo)}`)
      .then(res => res.json())
      .then(data => {
        if (data.error) {
          alert(data.error);
          return;
        }

        // Fill header / info
        document.querySelector(".info-name").textContent = data.name || "";
        document.querySelector(".info-dept").textContent = data.dept || "";
        document.querySelector(".info-title").textContent = data.title || "";
        document.querySelector(".info-grantno").textContent = data.grant_no || "";

        // Fill budget
        document.querySelector(".budget-year1").textContent = data.year1_budget ?? "";
        document.querySelector(".budget-year2").textContent = data.year2_budget ?? "";
        document.querySelector(".budget-total").textContent = data.total_budget ?? "";

        // Fill detailed budget rows
        const tbody = document.querySelector("#budget-table tbody");
        tbody.innerHTML = "";
        (data.report_rows || []).forEach((row, idx) => {
          const tr = document.createElement("tr");
          tr.innerHTML = `
            <td>${idx + 1}</td>
            <td>${row.head || ""}</td>
            <td>${row.sanction ?? ""}</td>
            <td>${row.expenditure ?? ""}</td>
            <td>${row.commitment ?? ""}</td>
            <td>${row.balance ?? ""}</td>
          `;
          tbody.appendChild(tr);
        });

        // totals row
        const totals = data.totals || {};
        const totalRow = document.createElement("tr");
        totalRow.className = "table-secondary fw-bold";
        totalRow.innerHTML = `
          <td colspan="2">Total</td>
          <td>${totals.budget ?? ""}</td>
          <td>${totals.expenditure ?? ""}</td>
          <td>${totals.commitment ?? ""}</td>
          <td>${totals.balance ?? ""}</td>
        `;
        tbody.appendChild(totalRow);

        // Fill expenditures table (if present)
        const expT = document.querySelector("#expenditure-table tbody");
        if (expT) {
          expT.innerHTML = "";
          (data.expenditures || []).forEach((e, i) => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
              <td>${i+1}</td>
              <td>${e.date ?? ""}</td>
              <td>${e.grant_no ?? ""}</td>
              <td>${e.head ?? ""}</td>
              <td>${e.voucher_no ?? ""}</td>
              <td>${e.particulars ?? ""}</td>
              <td>${e.amount ?? ""}</td>
              <td>${e.remarks ?? ""}</td>
            `;
            expT.appendChild(tr);
          });
        }
      })
      .catch(err => {
        console.error("Error fetching grant details:", err);
        alert("Error fetching grant details. Check console.");
      });
  });

  // Print helper: call window.print() (we hide controls via CSS @media print)
  window.printReport = function () { window.print(); };
});
