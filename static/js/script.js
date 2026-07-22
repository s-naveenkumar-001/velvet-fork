"use strict";

/* ---------- Nav toggle ---------- */
const navToggleBtn = document.querySelector("[data-menu-toggle-btn]");
const navbar = document.querySelector("[data-navbar]");
if (navToggleBtn && navbar) {
  navToggleBtn.addEventListener("click", () => {
    navbar.classList.toggle("active");
    navToggleBtn.classList.toggle("active");
  });
}

/* ---------- Search box ---------- */
const searchBtn = document.querySelector("[data-search-btn]");
const searchContainer = document.querySelector("[data-search-container]");
const searchCloseBtn = document.querySelector("[data-search-close-btn]");
if (searchBtn && searchContainer) {
  searchBtn.addEventListener("click", () => searchContainer.classList.add("active"));
  searchCloseBtn.addEventListener("click", () => searchContainer.classList.remove("active"));
}

/* ---------- Back to top ---------- */
const backTopBtn = document.querySelector("[data-back-top-btn]");
window.addEventListener("scroll", () => {
  if (backTopBtn) backTopBtn.classList.toggle("active", window.scrollY > 400);
});

/* ---------- Menu filter ---------- */
const filterBtns = document.querySelectorAll(".filter-btn");
const menuCards = document.querySelectorAll(".food-menu-card");
filterBtns.forEach((btn) => {
  btn.addEventListener("click", () => {
    filterBtns.forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    const category = btn.dataset.filter;
    menuCards.forEach((card) => {
      const li = card.closest("li");
      const show = category === "all" || card.dataset.category === category;
      li.hidden = !show;
    });
  });
});

/* ---------- Reservation booking buttons scroll into view ---------- */
document.querySelectorAll("[data-scroll-to-reservation]").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.getElementById("reservation")?.scrollIntoView({ behavior: "smooth" });
  });
});

/* ---------- Helpers ---------- */
function showFormMessage(el, message, isError) {
  el.textContent = message;
  el.className = "form-message " + (isError ? "error" : "success");
}

async function postJSON(url, body) {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));
  return { ok: res.ok, status: res.status, data };
}

/* ---------- Reservation form ---------- */
const reservationForm = document.getElementById("reservation-form");
if (reservationForm) {
  reservationForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = new FormData(reservationForm);
    const msgEl = reservationForm.querySelector(".form-message");
    const submitBtn = reservationForm.querySelector("button[type=submit]");

    const date = formData.get("booking_date");
    const time = formData.get("booking_time");
    const payload = {
      customer_name: formData.get("full_name"),
      phone: formData.get("phone"),
      email: formData.get("email") || null,
      party_size: parseInt(formData.get("party_size"), 10),
      reservation_time: date && time ? `${date}T${time}` : "",
      special_requests: formData.get("message") || "",
    };

    submitBtn.disabled = true;
    const { ok, data } = await postJSON("/api/reservations", payload);
    submitBtn.disabled = false;

    if (ok) {
      showFormMessage(
        msgEl,
        `Table booked! Your confirmation code is ${data.confirmation_code}. Save it to modify or cancel later.`,
        false
      );
      reservationForm.reset();
    } else {
      showFormMessage(msgEl, data.message || "Could not complete the reservation.", true);
    }
  });
}

/* ---------- Feedback form ---------- */
const feedbackForm = document.getElementById("feedback-form");
if (feedbackForm) {
  feedbackForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = new FormData(feedbackForm);
    const msgEl = feedbackForm.querySelector(".form-message");
    const submitBtn = feedbackForm.querySelector("button[type=submit]");

    const payload = {
      customer_name: formData.get("customer_name") || null,
      email: formData.get("email") || null,
      rating: parseInt(formData.get("rating"), 10),
      comments: formData.get("comments"),
      related_order_code: formData.get("related_order_code") || null,
    };

    submitBtn.disabled = true;
    const { ok, data } = await postJSON("/api/feedback", payload);
    submitBtn.disabled = false;

    if (ok) {
      showFormMessage(msgEl, "Thank you! Your feedback has been received.", false);
      feedbackForm.reset();
    } else {
      showFormMessage(msgEl, data.message || "Could not submit feedback.", true);
    }
  });
}

/* ---------- Cart ---------- */
const cart = new Map(); // menu_item_id -> {name, price, quantity}

const cartFab = document.getElementById("cart-fab");
const cartCount = document.getElementById("cart-count");
const cartModal = document.getElementById("cart-modal");
const checkoutModal = document.getElementById("checkout-modal");

function renderCartFab() {
  const totalQty = [...cart.values()].reduce((sum, item) => sum + item.quantity, 0);
  if (cartCount) cartCount.textContent = totalQty;
  if (cartFab) cartFab.hidden = totalQty === 0;
}

document.querySelectorAll(".food-menu-card").forEach((card) => {
  const id = card.dataset.itemId;
  const name = card.dataset.itemName;
  const price = parseFloat(card.dataset.itemPrice);
  const qtyDisplay = card.querySelector(".qty-display");
  const decBtn = card.querySelector(".qty-dec");
  const incBtn = card.querySelector(".qty-inc");
  const addBtn = card.querySelector(".add-to-cart-btn");

  let qty = 1;
  decBtn?.addEventListener("click", () => {
    qty = Math.max(1, qty - 1);
    qtyDisplay.textContent = qty;
  });
  incBtn?.addEventListener("click", () => {
    qty = Math.min(20, qty + 1);
    qtyDisplay.textContent = qty;
  });
  addBtn?.addEventListener("click", () => {
    const existing = cart.get(id);
    if (existing) {
      existing.quantity += qty;
    } else {
      cart.set(id, { name, price, quantity: qty });
    }
    renderCartFab();
    addBtn.textContent = "Added!";
    setTimeout(() => (addBtn.textContent = "Add to Cart"), 900);
  });
});

function renderCartModal() {
  const linesEl = document.getElementById("cart-lines");
  const totalEl = document.getElementById("cart-total-value");
  if (!linesEl) return;
  linesEl.replaceChildren();
  let total = 0;
  cart.forEach((item, id) => {
    const lineTotal = item.price * item.quantity;
    total += lineTotal;

    const row = document.createElement("div");
    row.className = "cart-line";

    const nameSpan = document.createElement("span");
    nameSpan.textContent = `${item.name} × ${item.quantity}`;

    const priceSpan = document.createElement("span");
    priceSpan.append(`$${lineTotal.toFixed(2)} `);

    const removeBtn = document.createElement("button");
    removeBtn.type = "button";
    removeBtn.className = "remove-line";
    removeBtn.dataset.remove = id;
    removeBtn.textContent = "Remove";
    priceSpan.appendChild(removeBtn);

    row.append(nameSpan, priceSpan);
    linesEl.appendChild(row);
  });
  if (totalEl) totalEl.textContent = `$${total.toFixed(2)}`;
  linesEl.querySelectorAll("[data-remove]").forEach((btn) => {
    btn.addEventListener("click", () => {
      cart.delete(btn.dataset.remove);
      renderCartFab();
      renderCartModal();
    });
  });
}

cartFab?.addEventListener("click", () => {
  renderCartModal();
  cartModal.hidden = false;
});

document.querySelectorAll("[data-close-modal]").forEach((btn) => {
  btn.addEventListener("click", () => {
    btn.closest(".modal-overlay").hidden = true;
  });
});

document.getElementById("checkout-btn")?.addEventListener("click", () => {
  cartModal.hidden = true;
  checkoutModal.hidden = false;
});

const orderTypeRadios = document.querySelectorAll('input[name="order_type"]');
const deliveryAddressGroup = document.getElementById("delivery-address-group");
orderTypeRadios.forEach((radio) => {
  radio.addEventListener("change", () => {
    deliveryAddressGroup.hidden = radio.value !== "delivery" || !radio.checked;
  });
});

const checkoutForm = document.getElementById("checkout-form");
if (checkoutForm) {
  checkoutForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = new FormData(checkoutForm);
    const msgEl = checkoutForm.querySelector(".form-message");
    const submitBtn = checkoutForm.querySelector("button[type=submit]");

    if (cart.size === 0) {
      showFormMessage(msgEl, "Your cart is empty.", true);
      return;
    }

    const payload = {
      customer_name: formData.get("customer_name"),
      phone: formData.get("phone"),
      email: formData.get("email") || null,
      order_type: formData.get("order_type"),
      delivery_address: formData.get("delivery_address") || null,
      notes: formData.get("notes") || "",
      items: [...cart.values()].map((item) => ({
        menu_item_name: item.name,
        quantity: item.quantity,
      })),
    };

    submitBtn.disabled = true;
    const { ok, data } = await postJSON("/api/orders", payload);
    submitBtn.disabled = false;

    if (ok) {
      showFormMessage(
        msgEl,
        `Order placed! Confirmation code: ${data.confirmation_code}. Total: $${data.total_amount.toFixed(2)}.`,
        false
      );
      cart.clear();
      renderCartFab();
      checkoutForm.reset();
    } else {
      showFormMessage(msgEl, data.message || "Could not place the order.", true);
    }
  });
}
