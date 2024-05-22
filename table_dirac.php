<?php
$jsonString = file_get_contents(METADATA_PATH);
$metadata = json_decode($jsonString, true);

$lastUpdate = $metadata['last_file_update'];
$samples = $metadata['transformations'];

$nLines = count($samples);
$nCols = 0;
$colNames = array('ID');
if ($nLines > 0) {
  $sampleIDs = array_keys($samples);
  $colNames = array_merge(
      $colNames,
      array_keys($samples[$sampleIDs[0]])
  );
  $nCols = count($colNames);
}
?>
      <p>Last update: <?= $lastUpdate ?></p>

      <div class="mt-5 input-group input-group-lg">
        <span class="input-group-text" id="sample-search-label">Name</span>
        <input type="text"
               class="form-control"
               id="sample-search-input"
               placeholder="Search in sample names..."
               aria-label="Search in sample names"
               aria-describedby="sample-search-label"
               onkeyup="search()">
      </div>

      <button type="button"
              class="btn btn-light float-end mt-4"
              id="table-expand-btn">Expand table</button>

      <table class="table table-striped table-hover mt-1" id="sample-table">
        <thead class="bg-blue">
          <tr class="header">
          <?php for ($i = 0; $i < $nCols; $i++): ?>
            <th><?= $colNames[$i] ?></th>
          <?php endfor ?>
          </tr>
        </thead>
        <tbody>
        <?php for ($i = 0; $i < $nLines; $i++): ?>
          <tr>
            <td><?= $sampleIDs[$i] ?></td>
            <?php for ($j = 1; $j < $nCols - 1; $j++): ?>
            <td><?= $samples[$sampleIDs[$i]][$colNames[$j]] ?></td>
            <?php endfor ?>
            <td>
              <?php foreach ($samples[$sampleIDs[$i]]["path"] as $path) {echo "$path";} ?>
            </td>
          </tr>
        <?php endfor ?>
        </tbody>
      </table>

      <div class="container">
        <?php for ($i = 0; $i < $nLines; $i++): ?>
        <div class="row">
          <div class="col info-box">
            <div class="row">
              <div class="col p-3 text-center info-box-top">
                aa
              </div>
            </div>
            <div class="row">
              <div class="col p-3 text-center info-box-bottom">
                bb
              </div>
            </div>
          </div>
        </div>
        <?php endfor ?>
      </div>


      <script src="<?= BASE_URL ?>/js/table.js"></script>
