document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("upload-form");

  form.addEventListener("submit", async function (e) {
    e.preventDefault();

    const fileInput = document.getElementById("chat-file");
    const file = fileInput.files[0];

    if (!file) {
      alert("Please select a file first.");
      return;
    }

    const formData = new FormData();
    formData.append("chat", file);

    try {
      const response = await fetch("/analyze", { method: "POST", body: formData });

      if (!response.ok) {
        throw new Error("Server error: " + response.statusText);
      }

      const result = await response.json();
      window.latestResults = result;
      displayResults(result);
    } catch (error) {
      console.error("Error uploading file:", error);
      alert("Something went wrong. Check the console for details.");
    }
  });

  function displayResults(data) {
    const container = document.getElementById("results");
    let html = "";

    // Message counts
    if (data.message_counts) {
      html += `<h2>📊 Message Counts</h2>
      <canvas id="msgChart"></canvas>
      <ul>${data.message_counts.map(x => `<li><strong>${x.Name}</strong>: ${x.message_count}</li>`).join("")}</ul>`;
    }

    // Word counts
    if (data.word_counts) {
      html += `<h2>📝 Word Counts</h2>
      <canvas id="wordChart"></canvas>
      <ul>${data.word_counts.map(x => `<li><strong>${x.Name}</strong>: ${x.word_count}</li>`).join("")}</ul>`;
    }

    // Most active hour
    if (data.most_active_hour) {
      html += `<h2>⏰ Most Active Hour</h2>
      <ul>${data.most_active_hour.map(x => `<li><strong>${x.Name}</strong> at ${x.hour}:00 → ${x.count} messages</li>`).join("")}</ul>`;
    }

    // Longest gap hours
    if (data.longest_gap_hours) {
      html += `<h2>⏱️ Longest Gap (hours per user)</h2>
      <ul>${data.longest_gap_hours.map(x => `<li><strong>${x.Name}</strong>: ${x.gap.toFixed(2)} hours</li>`).join("")}</ul>`;
    }

    // Absence periods
    if (data.absence_periods) {
      html += `<h2>🚫 Absence Periods</h2>
      ${data.absence_periods.map(r => `
        <p><strong>${r.Name}</strong> absent for ${r.gap.toFixed(2)} minutes<br>
        From ${r.absence_start} → ${r.absence_end}</p>`).join("")}`;
    }

    // Morning vs Evening
    if (data.morning_evening) {
      html += `<h2>🌅 Morning vs Evening</h2>
      <h3>Morning</h3>
      <ul>${Object.entries(data.morning_evening.morning).map(([name,count]) => `<li>${name}: ${count}</li>`).join("")}</ul>
      <h3>Evening</h3>
      <ul>${Object.entries(data.morning_evening.evening).map(([name,count]) => `<li>${name}: ${count}</li>`).join("")}</ul>`;
    }

    // Average message length
    if (data.avg_message_length) {
      html += `<h2>📏 Average Message Length</h2>
      <ul>${Object.entries(data.avg_message_length).map(([name,avg]) => `<li>${name}: ${avg.toFixed(1)} chars</li>`).join("")}</ul>`;
    }

    // Longest message by char
    if (data.longest_message_by_char) {
      html += `<h2>📝 Longest Message (by characters)</h2>
      <p><strong>${data.longest_message_by_char.sender}</strong> (${data.longest_message_by_char.char_count} chars)</p>
      <blockquote>${data.longest_message_by_char.preview}...</blockquote>`;
    }

    // Longest message by word
    if (data.longest_message_by_word) {
      html += `<h2>📝 Longest Message (by words)</h2>
      <p><strong>${data.longest_message_by_word.sender}</strong> (${data.longest_message_by_word.word_count} words)</p>
      <blockquote>${data.longest_message_by_word.preview}...</blockquote>`;
    }

    // Keyword mentions
    if (data.keyword_mentions) {
      html += `<h2>🔎 Keyword Mentions</h2>`;
      Object.entries(data.keyword_mentions).forEach(([kw, counts]) => {
        html += `<h3>${kw}</h3><ul>${Object.entries(counts).map(([name,count]) => `<li>${name}: ${count}</li>`).join("")}</ul>`;
      });
    }

    // First message
    if (data.first_message) {
      html += `<h2>📖 First Message</h2>
      <p><strong>${data.first_message.sender}</strong> at ${data.first_message.timestamp}</p>
      <blockquote>${data.first_message.message}</blockquote>`;
    }

    // Swear word counts
    if (data.swear_word_counts) {
      html += `<h2>🤬 Swear Word Counts</h2>
      <canvas id="swearChart"></canvas>`;
      Object.entries(data.swear_word_counts).forEach(([sw, counts]) => {
        html += `<h3>${sw}</h3><ul>${Object.entries(counts).map(([name,count]) => `<li>${name}: ${count}</li>`).join("")}</ul>`;
      });
    }

    // Download buttons
    html += `<button id="download-json">⬇️ Download JSON</button>
             <button id="download-csv">⬇️ Download CSV</button>`;

    container.innerHTML = html;

    // Charts
    if (data.message_counts) {
      createBarChart("msgChart", "Messages", data.message_counts.map(x => x.Name), data.message_counts.map(x => x.message_count));
    }
    if (data.word_counts) {
      createBarChart("wordChart", "Words", data.word_counts.map(x => x.Name), data.word_counts.map(x => x.word_count));
    }
    if (data.swear_word_counts) {
      const swearNames = Object.keys(data.swear_word_counts.shit || {});
      const swearWords = Object.keys(data.swear_word_counts);
      const datasets = swearWords.map(word => ({
        label: word,
        data: swearNames.map(name => data.swear_word_counts[word][name] || 0),
        backgroundColor: getColor(word)
      }));
      createStackedChart("swearChart", swearNames, datasets);
    }

    // Downloads
    document.getElementById("download-json").addEventListener("click", () => {
      const blob = new Blob([JSON.stringify(window.latestResults, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "chat_analysis.json";
      a.click();
      URL.revokeObjectURL(url);
    });

    document.getElementById("download-csv").addEventListener("click", () => {
      const rows = [["Category","Name","Metric","Value"]];
      if (data.message_counts) data.message_counts.forEach(x => rows.push(["Message Counts",x.Name,"messages",x.message_count]));
      if (data.word_counts) data.word_counts.forEach(x => rows.push(["Word Counts",x.Name,"words",x.word_count]));
      if (data.longest_gap_hours) data.longest_gap_hours.forEach(x => rows.push(["Longest Gap Hours",x.Name,"hours",x.gap]));
      if (data.absence_periods) data.absence_periods.forEach(r => rows.push(["Absence Periods",r.Name,"gap_minutes",r.gap]));
      if (data.avg_message_length) Object.entries(data.avg_message_length).forEach(([n,v]) => rows.push(["Average Message Length",n,"chars",v]));
      if (data.longest_message_by_char) rows.push(["Longest Message by Char",data.longest_message_by_char.sender,"chars",data.longest_message_by_char.char_count]);
      if (data.longest_message_by_word) rows.push(["Longest Message by Word",data.longest_message_by_word.sender,"words",data.longest_message_by_word.word_count]);
      if (data.keyword_mentions) Object.entries(data.keyword_mentions).forEach(([kw,counts]) => {
        Object.entries(counts).forEach(([n,c]) => rows.push(["Keyword Mentions",n,kw,c]));
      });
      if (data.first_message) rows.push(["First Message",data.first_message.sender,"text",data.first_message.message]);
            if (data.swear_word_counts) {
        Object.entries(data.swear_word_counts).forEach(([sw, counts]) => {
          Object.entries(counts).forEach(([name, count]) => {
            rows.push(["Swear Words", name, sw, count]);
          });
        });
      }

      const csvContent = rows
        .map(r => r.map(v => `"${String(v).replace(/"/g, '""')}"`).join(","))
        .join("\n");

      const blob = new Blob([csvContent], { type: "text/csv" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "chat_analysis.csv";
      a.click();
      URL.revokeObjectURL(url);
    });
  }

  // Chart helpers
  function createBarChart(canvasId, label, labels, values) {
    const el = document.getElementById(canvasId);
    if (!el) return;
    new Chart(el, {
      type: "bar",
      data: {
        labels,
        datasets: [{
          label,
          data: values,
          backgroundColor: "rgba(75, 192, 192, 0.6)"
        }]
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } }
      }
    });
  }

  function createStackedChart(canvasId, labels, datasets) {
    const el = document.getElementById(canvasId);
    if (!el) return;
    new Chart(el, {
      type: "bar",
      data: { labels, datasets },
      options: {
        responsive: true,
        plugins: { legend: { position: "top" } },
        scales: { x: { stacked: true }, y: { stacked: true } }
      }
    });
  }

  function getColor(word) {
    const colors = {
      shit: "rgba(255, 99, 132, 0.6)",
      fuck: "rgba(54, 162, 235, 0.6)",
      cunt: "rgba(255, 206, 86, 0.6)",
      sexotheque: "rgba(153, 102, 255, 0.6)"
    };
    return colors[word] || "rgba(75, 192, 192, 0.6)";
  }
});
