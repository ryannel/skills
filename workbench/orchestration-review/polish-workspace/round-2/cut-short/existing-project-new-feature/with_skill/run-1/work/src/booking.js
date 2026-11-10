// A booking: one customer, one stylist, one time slot.
export function createBooking(customer, stylist, slot) {
  return { customer, stylist, slot, status: "confirmed" };
}
