// Filter sample information boxed based on the filter string
const filterSamples = function() {
  const filterStr = this.value.toLowerCase();
  const sampleBoxes = document.getElementsByClassName("sample-box");

  for (let sampleBox of sampleBoxes) {
    const sampleName = sampleBox.dataset.sampleName.toLowerCase();
    if (sampleName.indexOf(filterStr) > -1) {
      sampleBox.style.display = "";
    } else {
      sampleBox.style.display = "none";
    }
  }
};

document.getElementById("sample-filter").addEventListener('keyup', filterSamples);


// Event listener to expand/colapse the sample information boxes
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
  sampleElems[i].addEventListener('dblclick', moreInfoToggle);
  sampleElems[i].addEventListener('mousedown', function(event) {
    if (event.detail > 1) {
      event.preventDefault();
      // of course, you still do not know what you prevent here...
      // You could also check event.ctrlKey/event.shiftKey/event.altKey
      // to not prevent something useful.
      // from:
      // https://stackoverflow.com/questions/880512/prevent-text-selection-after-double-click
    }
  }, false);
}
