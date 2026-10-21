/**
 * Hospital Appointment System - FullCalendar Integration
 */

document.addEventListener('DOMContentLoaded', () => {
  const calendarEl = document.getElementById('appointmentCalendar');
  if (!calendarEl) return;

  const calendar = new FullCalendar.Calendar(calendarEl, {
    initialView: 'dayGridMonth',
    headerToolbar: {
      left: 'prev,next today',
      center: 'title',
      right: 'dayGridMonth,timeGridWeek,timeGridDay'
    },
    themeSystem: 'standard',
    events: '/api/calendar/events',
    nowIndicator: true,
    slotMinTime: '08:00:00',
    slotMaxTime: '20:00:00',
    allDaySlot: false,
    eventTimeFormat: {
      hour: '2-digit',
      minute: '2-digit',
      meridiem: 'short'
    },
    eventClick: function(info) {
      showCalendarEventModal(info.event);
    },
    eventDidMount: function(info) {
      // Add tooltip styling or title attribute
      const props = info.event.extendedProps;
      info.el.setAttribute('title', `${info.event.title} - ${props.reason}`);
    }
  });

  calendar.render();
});

function showCalendarEventModal(event) {
  const modal = document.getElementById('calendarEventModal');
  if (!modal) return;

  const props = event.extendedProps;

  document.getElementById('calModalTitle').textContent = event.title;
  document.getElementById('calModalDoctor').textContent = props.doctorName || 'N/A';
  document.getElementById('calModalSpecialization').textContent = props.doctorSpecialization || 'General Medicine';
  document.getElementById('calModalPatient').textContent = props.patientName || 'N/A';
  document.getElementById('calModalTime').textContent = `${event.start.toLocaleDateString()} at ${event.start.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
  document.getElementById('calModalReason').textContent = props.reason || 'General Medical Consultation';
  document.getElementById('calModalFee').textContent = `₹${props.fee || 0}`;

  const statusEl = document.getElementById('calModalStatus');
  statusEl.className = `badge badge-${props.status}`;
  statusEl.textContent = props.status;

  const reasonRow = document.getElementById('calModalCancelRow');
  if (props.status === 'cancelled' && props.cancellationReason) {
    reasonRow.style.display = 'block';
    document.getElementById('calModalCancelReason').textContent = props.cancellationReason;
  } else if (reasonRow) {
    reasonRow.style.display = 'none';
  }

  openModal('calendarEventModal');
}
