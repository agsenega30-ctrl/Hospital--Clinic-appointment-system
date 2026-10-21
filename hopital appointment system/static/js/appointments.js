/**
 * Hospital Appointment System - Appointment Booking & Scheduling Operations
 */

document.addEventListener('DOMContentLoaded', () => {
  initSlotBooking();
  initCancellationModals();
  initRescheduleModals();
  initStatusChangeActions();
});

/**
 * Handles Dynamic Slot Availability Loading on Book Appointment Page
 */
function initSlotBooking() {
  const doctorSelect = document.getElementById('doctorSelect');
  const dateInput = document.getElementById('appointmentDate');
  const slotsContainer = document.getElementById('slotsContainer');
  const slotsLoading = document.getElementById('slotsLoading');
  const startTimeInput = document.getElementById('startTimeInput');
  const submitBtn = document.getElementById('submitBookingBtn');

  if (!doctorSelect || !dateInput || !slotsContainer) return;

  async function loadSlots() {
    const doctorId = doctorSelect.value;
    const dateStr = dateInput.value;

    if (!doctorId || !dateStr) {
      slotsContainer.innerHTML = '<div style="color: #64748b; font-size: 0.9rem; padding: 10px 0;">Please select both a doctor and a date to view available time slots.</div>';
      if (submitBtn) submitBtn.disabled = true;
      if (startTimeInput) startTimeInput.value = '';
      return;
    }

    if (slotsLoading) slotsLoading.style.display = 'block';
    slotsContainer.innerHTML = '';
    if (submitBtn) submitBtn.disabled = true;
    if (startTimeInput) startTimeInput.value = '';

    try {
      const res = await fetch(`/api/doctors/${doctorId}/slots?date=${dateStr}`);
      const data = await res.json();
      if (slotsLoading) slotsLoading.style.display = 'none';

      if (!data.success) {
        slotsContainer.innerHTML = `<div class="alert alert-warning" style="margin: 0;">${data.error || 'Failed to fetch slots'}</div>`;
        return;
      }

      if (data.message && (!data.slots || data.slots.length === 0)) {
        slotsContainer.innerHTML = `<div class="alert alert-info" style="margin: 0;">${data.message}</div>`;
        return;
      }

      const availableSlots = data.slots.filter(s => s.is_available);
      if (availableSlots.length === 0) {
        slotsContainer.innerHTML = '<div class="alert alert-warning" style="margin: 0;">No available slots remaining on this day. Please choose another date.</div>';
        return;
      }

      const grid = document.createElement('div');
      grid.className = 'slots-grid';

      data.slots.forEach(slot => {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'slot-btn';
        btn.textContent = slot.start_time;

        if (!slot.is_available) {
          btn.disabled = true;
          btn.title = slot.reason;
        } else {
          btn.addEventListener('click', () => {
            document.querySelectorAll('.slot-btn').forEach(b => b.classList.remove('selected'));
            btn.classList.add('selected');
            startTimeInput.value = slot.start_time;
            if (submitBtn) submitBtn.disabled = false;
          });
        }
        grid.appendChild(btn);
      });

      slotsContainer.appendChild(grid);
    } catch (err) {
      if (slotsLoading) slotsLoading.style.display = 'none';
      slotsContainer.innerHTML = '<div class="alert alert-danger">Error connecting to server. Please try again.</div>';
      console.error(err);
    }
  }

  doctorSelect.addEventListener('change', loadSlots);
  dateInput.addEventListener('change', loadSlots);

  // Initial trigger if values pre-filled
  if (doctorSelect.value && dateInput.value) {
    loadSlots();
  }
}

/**
 * Handles Appointment Cancellation Dialogs
 */
let currentCancelAppointmentId = null;

function initCancellationModals() {
  document.querySelectorAll('.btn-open-cancel').forEach(btn => {
    btn.addEventListener('click', function() {
      currentCancelAppointmentId = this.dataset.appointmentId;
      const modal = document.getElementById('cancelModal');
      if (modal) {
        document.getElementById('cancelReasonInput').value = '';
        openModal('cancelModal');
      }
    });
  });

  const confirmCancelBtn = document.getElementById('confirmCancelBtn');
  if (confirmCancelBtn) {
    confirmCancelBtn.addEventListener('click', async () => {
      if (!currentCancelAppointmentId) return;

      const reason = document.getElementById('cancelReasonInput').value.trim();
      confirmCancelBtn.disabled = true;
      confirmCancelBtn.textContent = 'Cancelling...';

      try {
        const res = await fetchWithCsrf(`/api/appointments/${currentCancelAppointmentId}/cancel`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ reason: reason })
        });
        const data = await res.json();

        if (data.success) {
          showToast('Appointment cancelled successfully', 'success');
          closeModal('cancelModal');
          setTimeout(() => window.location.reload(), 800);
        } else {
          showToast(data.error || 'Failed to cancel appointment', 'danger');
          confirmCancelBtn.disabled = false;
          confirmCancelBtn.textContent = 'Confirm Cancellation';
        }
      } catch (err) {
        showToast('Network error while cancelling', 'danger');
        confirmCancelBtn.disabled = false;
        confirmCancelBtn.textContent = 'Confirm Cancellation';
      }
    });
  }
}

/**
 * Handles Appointment Rescheduling Modal
 */
let currentRescheduleAppointmentId = null;
let currentRescheduleDoctorId = null;

function initRescheduleModals() {
  document.querySelectorAll('.btn-open-reschedule').forEach(btn => {
    btn.addEventListener('click', function() {
      currentRescheduleAppointmentId = this.dataset.appointmentId;
      currentRescheduleDoctorId = this.dataset.doctorId;

      const modal = document.getElementById('rescheduleModal');
      if (modal) {
        document.getElementById('rescheduleDateInput').value = '';
        document.getElementById('rescheduleSlotsContainer').innerHTML = '<div style="color: #64748b; font-size: 0.88rem;">Select a new date above to load available slots.</div>';
        document.getElementById('confirmRescheduleBtn').disabled = true;
        openModal('rescheduleModal');
      }
    });
  });

  const rescheduleDateInput = document.getElementById('rescheduleDateInput');
  const rescheduleSlotsContainer = document.getElementById('rescheduleSlotsContainer');
  const confirmRescheduleBtn = document.getElementById('confirmRescheduleBtn');
  let selectedNewTime = '';

  if (rescheduleDateInput && rescheduleSlotsContainer) {
    rescheduleDateInput.addEventListener('change', async () => {
      const dateStr = rescheduleDateInput.value;
      if (!dateStr || !currentRescheduleDoctorId) return;

      rescheduleSlotsContainer.innerHTML = '<div style="color: #64748b;">Loading slots...</div>';
      confirmRescheduleBtn.disabled = true;
      selectedNewTime = '';

      try {
        const res = await fetch(`/api/doctors/${currentRescheduleDoctorId}/slots?date=${dateStr}`);
        const data = await res.json();

        if (!data.success || !data.slots || data.slots.length === 0) {
          rescheduleSlotsContainer.innerHTML = `<div class="alert alert-warning" style="margin: 0;">${data.message || data.error || 'No slots available on this date'}</div>`;
          return;
        }

        const available = data.slots.filter(s => s.is_available);
        if (available.length === 0) {
          rescheduleSlotsContainer.innerHTML = '<div class="alert alert-warning" style="margin: 0;">All slots are booked or unavailable on this date.</div>';
          return;
        }

        const grid = document.createElement('div');
        grid.className = 'slots-grid';

        data.slots.forEach(slot => {
          const btn = document.createElement('button');
          btn.type = 'button';
          btn.className = 'slot-btn';
          btn.textContent = slot.start_time;

          if (!slot.is_available) {
            btn.disabled = true;
          } else {
            btn.addEventListener('click', () => {
              rescheduleSlotsContainer.querySelectorAll('.slot-btn').forEach(b => b.classList.remove('selected'));
              btn.classList.add('selected');
              selectedNewTime = slot.start_time;
              confirmRescheduleBtn.disabled = false;
            });
          }
          grid.appendChild(btn);
        });

        rescheduleSlotsContainer.innerHTML = '';
        rescheduleSlotsContainer.appendChild(grid);
      } catch (err) {
        rescheduleSlotsContainer.innerHTML = '<div class="alert alert-danger">Error loading slots.</div>';
      }
    });
  }

  if (confirmRescheduleBtn) {
    confirmRescheduleBtn.addEventListener('click', async () => {
      if (!currentRescheduleAppointmentId || !rescheduleDateInput.value || !selectedNewTime) return;

      confirmRescheduleBtn.disabled = true;
      confirmRescheduleBtn.textContent = 'Rescheduling...';

      try {
        const res = await fetchWithCsrf(`/api/appointments/${currentRescheduleAppointmentId}/reschedule`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            new_date: rescheduleDateInput.value,
            new_start_time: selectedNewTime
          })
        });
        const data = await res.json();

        if (data.success) {
          showToast('Appointment rescheduled successfully!', 'success');
          closeModal('rescheduleModal');
          setTimeout(() => window.location.reload(), 800);
        } else {
          showToast(data.error || 'Failed to reschedule', 'danger');
          confirmRescheduleBtn.disabled = false;
          confirmRescheduleBtn.textContent = 'Confirm Reschedule';
        }
      } catch (err) {
        showToast('Network error while rescheduling', 'danger');
        confirmRescheduleBtn.disabled = false;
        confirmRescheduleBtn.textContent = 'Confirm Reschedule';
      }
    });
  }
}

/**
 * Handles Doctor/Admin quick status changes (Confirm, Mark Completed)
 */
function initStatusChangeActions() {
  document.querySelectorAll('.btn-update-status').forEach(btn => {
    btn.addEventListener('click', async function() {
      const appDocId = this.dataset.appointmentId;
      const newStatus = this.dataset.status;

      if (!confirm(`Are you sure you want to mark this appointment as ${newStatus}?`)) {
        return;
      }

      this.disabled = true;
      try {
        const res = await fetchWithCsrf(`/api/appointments/${appDocId}/status`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ status: newStatus })
        });
        const data = await res.json();
        if (data.success) {
          showToast(`Status updated to ${newStatus}`, 'success');
          setTimeout(() => window.location.reload(), 600);
        } else {
          showToast(data.error || 'Update failed', 'danger');
          this.disabled = false;
        }
      } catch (err) {
        showToast('Error communicating with server', 'danger');
        this.disabled = false;
      }
    });
  });
}
