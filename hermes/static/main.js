async function updateStations() {
    const selectedSchedules = Array.from(document.querySelectorAll('#schedule-widget input:checked'))
        .map(input => input.value);

    const stationWidget = document.getElementById('station-widget');
    stationWidget.innerHTML = '<div class="widget-title">Stations:</div>';

    for (const schedule of selectedSchedules) {
        const response = await fetch(`/stations/${schedule}`);
        const stations = await response.json();

        stations.forEach(station => {
            const stationItem = document.createElement('div');
            stationItem.className = 'widget-item';
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.value = station.id;
            checkbox.checked = true;

            const label = document.createElement('label');
            label.textContent = `${station.callsign} (${station.location})`;

            stationItem.appendChild(checkbox);
            stationItem.appendChild(label);
            stationWidget.appendChild(stationItem);
        });
    }
}

document.getElementById('filter-button').addEventListener('click', async () => {
    const selectedStations = Array.from(document.querySelectorAll('#station-widget input:checked'))
        .map(input => input.value);
    const startDay = document.getElementById('start-day').value;
    const startHour = document.getElementById('start-hour').value;
    const startMinute = document.getElementById('start-minute').value;
    const endHour = document.getElementById('end-hour').value;
    const endMinute = document.getElementById('end-minute').value;
    const startTime = `${startHour}${startMinute}`
    const endTime = `${endHour}${endMinute}`

    const response = await fetch('/filter', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ start_day: startDay, start_time: startTime, end_time: endTime, station_ids: selectedStations})
    });

    const results = await response.json();
    const scheduleTable = document.getElementById('schedule-table');
    if (results.length === 0) {
        scheduleTable.innerHTML = '<p>No transmissions match parameters!</p>';
    } else {
        scheduleTable.innerHTML = `
            <table>
                <thead>
                    <tr>
                        <th>Time</th>
                        <th>Transmission</th>
                        <th>Station</th>
                        <th>Frequency (kHz)</th>
                    </tr>
                </thead>
                <tbody>
                    ${results.map(result => `
                        <tr>
                            <td>${result.day} ${result.time}</td>
                            <td>${result.name}</td>
                            <td>${result.station}</td>
                            <td>${result.frequencies.join('<br>')}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>`;
    }
});

function presetDayTime() {
    const now = new Date();
    const startDay = now.toUTCString().split(' ')[0].slice(0, -1);
    const utcTime = now.toUTCString().split(' ')[4];
    const timeString = utcTime.substring(0, 5);
    const startHour = parseInt(timeString.split(':')[0]);
    const endHour = (startHour + 2) % 24;

    console.log("startDay", startDay);
    document.getElementById('start-day').value = startDay;
    document.getElementById('start-hour').value = startHour.toString().padStart(2, '0');
    document.getElementById('end-hour').value = endHour.toString().padStart(2, '0');
}

window.onload = function () {
    updateStations();

    const currentUtcTime = document.getElementById('current-utc-time');


    function updateCurrentUtcTime() {
        const now = new Date();
        const utcDay = now.toUTCString().split(' ')[0]; // Example: 'Fri'
        const utcTime = now.toUTCString().split(' ')[4]; // Example: '00:19:00'
        const timeString = `${utcDay} ${utcTime.substring(0, 5)}`; // 'Fri 00:19'
        if (!currentUtcTime) {
            throw new Error('currentUtcTime not defined')
        }
        currentUtcTime.textContent = `Current time: ${timeString}`;
    }

    updateCurrentUtcTime();
    setInterval(updateCurrentUtcTime, 10000); // Update every ten seconds

    presetDayTime();
};
