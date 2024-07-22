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
    sampleElems[i].addEventListener('click', moreInfoToggle);
}
