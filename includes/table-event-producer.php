<?php
  $colNames = array();
  if ($evtType === 'gen') {
    $colNames = array('name', 'n-events',
                      'n-files', 'n-files-bad', 'n-files-eos', 'size',
                      'path', 'main-process', 'final-states',
                      'matching-param',
                      'cross-section');
  }
  if ($evtType === 'delphes') {
    $colNames = array('name', 'n-events', 'sum-of-weights',
                      'n-files', 'n-files-bad', 'n-files-eos', 'size',
                      'path', 'main-process', 'final-states',
                      'cross-section',
                      'k-factor', 'matching-eff');
  }
  if ($evtType === 'full-sim' && $acc === 'fcc-hh') {
    $colNames = array('name', 'n-events', 'n-files', 'n-files-eos',
                      'n-files-bad', 'size',
                      'aleksa', 'azaborow', 'cneubuse', 'djamin', 'helsens',
                      'jhrdinka', 'jkiesele', 'novaj', 'rastein', 'selvaggi',
                      'vavolkl');
  }

  $txt_file = file_get_contents($dataFilePath);
  $last_update = filemtime($dataFilePath);

  $rows = explode("\n", $txt_file);

  $samples = array();
  $nColsExpected = count($colNames);
  $totalInfo = array();
  foreach($rows as $rowId => $row) {
    // get row items
    $rowItems = explode(',,', $row);
    $nCols = count($rowItems);

    // Save and exclude total row
    if ($nCols > 1) {
      if ($rowItems[0] === 'total') {
        $totalInfo = $rowItems;
        continue;
      }
    }

    // Exclude non-standard rows
    if ($nCols != $nColsExpected) {
      continue;
    }

    // Parse row
    for ($i = 0; $i < $nCols; $i++) {
      $samples[$rowId][$colNames[$i]] = $rowItems[$i] ?? '';
    }

    // Add status for CSS
    $samples[$rowId]['status'] = 'stopped';
  }
?>

      <p class="mt-1 text-end text-secondary">
        Last update: <?= date('Y-M-d H:i T', $last_update) ?>.
      </p>

      <div class="mt-1 mb-5 input-group input-group-lg">
        <span class="input-group-text" id="sample-filter-label">Search</span>
        <input type="text"
               class="form-control"
               id="sample-filter"
               placeholder="Search in the samples..."
               aria-label="Search in sample names"
               aria-describedby="sample-filter-label">
      </div>

      <?php $tab_index = 0; ?>
      <div class="container">
        <?php foreach ($samples as $sample_id => $sample): ?>
        <?php $tab_index++; ?>
        <div class="row">
          <div class="col">
            <div class="mb-2 sample-box focus-ring rounded"
                 tabIndex="<?= $tab_index ?>"
                 data-search-string="<?= $sample["name"] ?>">
              <div class="sample-top rounded ps-4 bg-top-<?= $sample['status'] ?> bg-top-<?= $sample['status'] ?>-highlight">
                <div class="row">
                  <!-- Process name / Sample path -->
                  <div class="col p-3 text-left">
                    <?php if ($evtType === 'full-sim' && $acc === 'fcc-hh'): ?>
                    <b>Sample directory</b><br>
                    <?php else: ?>
                    <b>Process name</b><br>
                    <?php endif ?>
                    <?= $sample["name"] ?>
                  </div>
                  <!-- Number of events -->
                  <div class="col p-3 text-left">
                    <b>Number of events</b><br>
                    <?= $sample['n-events'] ?>
                  </div>
                  <!-- Sum of weights -->
                  <?php if (array_key_exists("sum-of-weights", $sample)): ?>
                  <div class="col p-3 text-left">
                    <b>Sum of weights</b><br>
                    <?= $sample["sum-of-weights"] ?>
                  </div>
                  <?php endif ?>
                </div>
                <div class="row">
                  <!-- Cross-section -->
                  <?php if (array_key_exists("cross-section", $sample)): ?>
                  <div class="col p-3 text-left">
                    <b>Cross-section</b><br>
                    <?php
                      if ($sample['cross-section'] < 0.) {
                        echo 'Unknown';
                      } else {
                        echo $sample['cross-section'], " pb";
                      } ?>
                  </div>
                  <?php endif ?>
                  <!-- K-factor -->
                  <?php if (array_key_exists("k-factor", $sample)): ?>
                  <div class="col p-3 text-left">
                    <b>K-factor</b><br>
                    <?= $sample["k-factor"] ?>
                  </div>
                  <?php endif ?>
                  <!-- Matching efficiency -->
                  <?php if (array_key_exists("matching-eff", $sample)): ?>
                  <div class="col p-3 text-left">
                    <b>Matching efficiency</b><br>
                    <?= $sample["matching-eff"] ?>
                  </div>
                  <?php endif ?>
                  <!-- Matching parameter -->
                  <?php if (array_key_exists("matching-param", $sample)): ?>
                  <div class="col p-3 text-left">
                    <b>Matching parameter</b><br>
                    <?= $sample["matching-param"] ?>
                  </div>
                  <?php endif ?>
                </div>
              </div>
              <div class="sample-bottom rounded-bottom ps-4 bg-bottom-<?= $sample['status'] ?>">
                <div class="row">
                  <!-- Main process -->
                  <?php if (array_key_exists("main-process", $sample)): ?>
                  <div class="col p-3 text-left">
                    <b>Main process</b><br>
                    <?= $sample["main-process"] ?>
                  </div>
                  <?php endif ?>
                  <!-- Final states -->
                  <?php if (array_key_exists("final-states", $sample)): ?>
                  <div class="col p-3 text-left">
                    <b>Final states</b><br>
                    <?= $sample["final-states"] ?>
                  </div>
                  <?php endif ?>
                </div>
                <div class="row">
                  <!-- Number of files produced-->
                  <div class="col p-3 text-left">
                    <b>Number of files produced</b><br>
                    <?= $sample["n-files"] ?>
                  </div>
                  <!-- Number of corrupted files -->
                  <div class="col p-3 text-left">
                    <b>Number of corrupted files</b><br>
                    <?= $sample['n-files-bad'] ?>
                  </div>
                  <!-- Number of files on EOS -->
                  <div class="col p-3 text-left">
                    <b>Number of files on EOS</b><br>
                    <?= $sample['n-files-eos'] ?>
                  </div>
                  <!-- Total size -->
                  <div class="col p-3 text-left">
                    <b>Total size</b><br>
                    <?= $sample['size'] ?> GB
                  </div>
                </div>
                <div class="row">
                  <?php if (array_key_exists("path", $sample)): ?>
                  <div class="col p-3 text-left">
                    <b>EOS Location</b>
                    <ul>
                      <li>
                        <span><?= $sample['path'] ?></span>
                        <div class="d-inline copy-sample-path"
                             data-path="<?= $sample['path'] ?>">
                          <i class="bi bi-clipboard align-baseline"
                             style="margin-left: 10px; color: darkred; cursor: pointer;"></i>
                          <i class="bi bi-clipboard-check align-baseline d-none"
                             style="margin-left: 10px; color: darkgreen; cursor: pointer;"></i>
                        </div>
                      </li>
                    </ul>
                  </div>
                  <?php endif ?>
                  <!-- Produced for -->
                  <?php if ($evtType === 'full-sim' && $acc === 'fcc-hh'): ?>
                  <div class="col p-3 text-left">
                    <b>Produced by</b><br>
                    <?php
                      $userList = '';
                      for ($i = 6; $i < $nColsExpected; $i++) {
                        if ($sample[$colNames[$i]] > 0) {
                          $userList .= '<code>' . $colNames[$i] . '</code>: ';
                          $userList .= $sample[$colNames[$i]]. ', ';
                        }
                      }
                      $userList = rtrim($userList);
                      $userList = rtrim($userList, ',');
                      echo $userList;
                    ?>
                  </div>
                  <?php endif ?>
                </div>
              </div>
            </div>
          </div>
        </div>
        <?php endforeach ?>
      </div>

      <?php if ($evtType === 'full-sim' && $acc === 'fcc-hh'): ?>
      <div class="container mt-3">
        <b>Total statistics:</b>
        <ul>
          <li>Number of samples: <?= count($samples) ?></li>
          <li>Number of all events: <?= $totalInfo[1] ?></li>
          <li>Number of produced files: <?= $totalInfo[2] ?></li>
          <li>Number of files on EOS: <?= $totalInfo[3] ?></li>
          <li>Number of corrupted files: <?= $totalInfo[4] ?></li>
          <li>Total size: <?= $totalInfo[5] ?> GB</li>
          <li>
            Produced by:
            <ul>
            <?php
              for ($i = 6; $i < $nColsExpected; $i++) {
                if ($totalInfo[$i] > 0) {
                  echo '<li><code>' . $colNames[$i] . '</code>: ';
                  echo $totalInfo[$i]. '</li>';
                }
              }
            ?>
            </ul>
          </li>
        </ul>
      </div>
      <?php else: ?>
      <?php if ($evtType === 'gen'): ?>
      <?php if (count($totalInfo) > 6): ?>
      <div class="container mt-3">
        <b>Total statistics:</b>
        <ul>
          <li>Number of samples: <?= count($samples) ?></li>
          <li>Number of all events: <?= $totalInfo[1] ?></li>
          <li>Number of produced files: <?= $totalInfo[2] ?></li>
          <li>Number of corrupted files: <?= $totalInfo[3] ?></li>
          <li>Number of files on EOS: <?= $totalInfo[4] ?></li>
          <li>Total size: <?= $totalInfo[5] ?> GB</li>
        </ul>
      </div>
      <?php endif ?>
      <?php else: ?>
      <?php if (count($totalInfo) > 7): ?>
      <div class="container mt-3">
        <b>Total statistics:</b>
        <ul>
          <li>Number of samples: <?= count($samples) ?></li>
          <li>Number of all events: <?= $totalInfo[1] ?></li>
          <li>Sum of all weights: <?= $totalInfo[2] ?></li>
          <li>Number of produced files: <?= $totalInfo[3] ?></li>
          <li>Number of corrupted files: <?= $totalInfo[4] ?></li>
          <li>Number of files on EOS: <?= $totalInfo[5] ?></li>
          <li>Total size: <?= $totalInfo[6] ?> GB</li>
        </ul>
      </div>
      <?php endif ?>
      <?php endif ?>
      <?php endif ?>

      <script src="<?= BASE_URL ?>/js/table.js"></script>
