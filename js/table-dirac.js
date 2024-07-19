function search() {
  // Declare variables
  // var input, filter, table, tr, td, i;
  const input = document.getElementById("sample-search-input");
  const filter = input.value.toUpperCase();
  const table = document.getElementById("sample-table");
  const tr = table.getElementsByTagName("tr");

  // Loop through all table rows, and hide those who don't match the search query
  for (let i = 0; i < tr.length; i++) {
    const td = tr[i].getElementsByTagName("td")[1];
    if (td) {
      if (td.innerHTML.toUpperCase().indexOf(filter) > -1) {
        tr[i].style.display = "";
      } else {
        tr[i].style.display = "none";
      }
    }
  }
}


// Event listener to expand/colapse the sample information
const sampleElems = document.getElementsByClassName("sample-box");

const moreInfoToggle = function() {
  const bottomElems = this.getElementsByClassName("sample-bottom");
  if (bottomElems.length < 1) {
    return;
  }
  const bottomElem = bottomElems[0];
  if (bottomElem.style.display === "") {
    bottomElem.style.display = "block";
    return;
  }
  if (bottomElem.style.display === "block") {
    bottomElem.style.display = "";
    return;
  }
};

for (var i = 0; i < sampleElems.length; i++) {
    sampleElems[i].addEventListener('click', moreInfoToggle, false);
}
