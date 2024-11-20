<?php
  // First lets try to load the samples from the JSON file
  $dataFilePathJSON = substr_replace($dataFilePath , 'json', strrpos($dataFilePath , '.') + 1);
  if (file_exists($dataFilePathJSON)) {
    $json_file = file_get_contents($dataFilePathJSON);
    if ($json_file === false) {
      die("ERROR: Can't read sample information!<br>Please contact site administrator(s).");
    }

    $json_data = json_decode($json_file, true);
    if ($json_data === null) {
      die("ERROR: Can't read sample information!<br>Please contact site administrator(s).");
    }

    $last_update = filemtime($dataFilePathJSON);

    $samples = $json_data['processes'];
    $totalInfo = $json_data['total'];

    // TODO: Remove this
    foreach($samples as &$sample) {
      // Add status for CSS
      if (!array_key_exists('status', $sample)) {
        $sample['status'] = 'unknown';
      }
    }
  } else {
    // Load the samples from the old txt files

    $colNames = array();
    if ($evtType === 'gen') {
      $colNames = array('process-name', 'n-events',
                        'n-files', 'n-files-bad', 'n-files-eos', 'size',
                        'path', 'description', 'comment',
                        'matching-param',
                        'cross-section');
    }
    if ($evtType === 'delphes') {
      $colNames = array('process-name', 'n-events', 'sum-of-weights',
                        'n-files', 'n-files-bad', 'n-files-eos', 'size',
                        'path', 'description', 'comment',
                        'cross-section',
                        'k-factor', 'matching-eff');
    }
    if ($evtType === 'full-sim' && $acc === 'fcc-hh') {
      $colNames = array('process-name', 'n-events', 'n-files', 'n-files-eos',
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
    $totalArr = array();
    foreach($rows as $rowId => $row) {
      // get row items
      $rowItems = explode(',,', $row);
      $nCols = count($rowItems);

      // Save and exclude total row
      if ($nCols > 1) {
        if ($rowItems[0] === 'total') {
          $totalArr = $rowItems;
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
    }

    foreach($samples as &$sample) {
      // Add status for CSS
      $sample['status'] = 'unknown';

      // Castings
      $sample['n-events'] = (int) str_replace(',', '', $sample['n-events']);
      if (array_key_exists("sum-of-weights", $sample)) {
        $sample['sum-of-weights'] = (float) str_replace(',', '', $sample['sum-of-weights']);
      }
      if (array_key_exists("cross-section", $sample)) {
        $sample['cross-section'] = (float) $sample['cross-section'];
      }
      $sample['n-files'] = (int) str_replace(',', '', $sample['n-files']);
      $sample['n-files-bad'] = (int) str_replace(',', '', $sample['n-files-bad']);
      $sample['n-files-eos'] = (int) str_replace(',', '', $sample['n-files-eos']);
    }

    $totalInfo = array();
    if ($evtType === 'gen') {
      $totalInfo['n-events'] = (int) str_replace(',', '', $totalArr[1]);
      $totalInfo['n-files'] = (int) str_replace(',', '', $totalArr[2]);
      $totalInfo['n-files-bad'] = (int) str_replace(',', '', $totalArr[3]);
      $totalInfo['n-files-eos'] = (int) str_replace(',', '', $totalArr[4]);
      $totalInfo['size'] = (float) $totalArr[5];
    }
    if ($evtType === 'delphes') {
      $totalInfo['n-events'] = (int) str_replace(',', '', $totalArr[1]);
      $totalInfo['sum-of-weights'] = (float) str_replace(',', '', $totalArr[2]);
      $totalInfo['n-files'] = (int) str_replace(',', '', $totalArr[3]);
      $totalInfo['n-files-bad'] = (int) str_replace(',', '', $totalArr[4]);
      $totalInfo['n-files-eos'] = (int) str_replace(',', '', $totalArr[5]);
      $totalInfo['size'] = (float) $totalArr[6];
    }
    if ($evtType === 'full-sim' && $acc === 'fcc-hh') {
      $totalInfo['n-events'] = (int) str_replace(',', '', $totalArr[1]);
      $totalInfo['n-files'] = (int) str_replace(',', '', $totalArr[2]);
      $totalInfo['n-files-eos'] = (int) str_replace(',', '', $totalArr[3]);
      $totalInfo['n-files-bad'] = (int) str_replace(',', '', $totalArr[4]);
      $totalInfo['size'] = (float) $totalArr[5];
      $totalInfo['produced-by'] = array();
      for ($i = 6; $i < $nColsExpected; $i++) {
        if ($totalArr[$i] > 0) {
          $totalInfo['produced-by'][$colNames[$i]] = (int) $totalArr[$i];
        }
      }
    }
  }

  // echo "<pre>";
  // print_r($samples);
  // echo "</pre>";
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
                 data-search-string="<?= $sample['process-name'] ?> <?php if(array_key_exists("description", $sample)) echo $sample['description']; ?> <?php if(array_key_exists("comment", $sample)) echo $sample['comment']; ?>">
              <div class="sample-top rounded ps-4 bg-top-<?= $sample['status'] ?> bg-top-<?= $sample['status'] ?>-highlight">
                <div class="row">
                  <!-- Process name / Sample path -->
                  <?php if ($evtType === 'full-sim' && $acc === 'fcc-hh'): ?>
                  <div class="col-8 p-3 text-left">
                    <b>Sample directory</b><br>
                    <?= $sample["process-name"] ?>
                  </div>
                  <?php else: ?>
                  <div class="col p-3 text-left">
                    <b>Process name</b><br>
                    <?= $sample["process-name"] ?>
                  </div>
                  <?php endif ?>
                  <!-- Number of events -->
                  <div class="col p-3 text-left">
                    <b>Number of events</b><br>
                    <?php echo number_format($sample['n-events'], 0, '.', '&thinsp;'); ?>
                  </div>
                  <!-- Sum of weights -->
                  <?php if (array_key_exists("sum-of-weights", $sample)): ?>
                  <div class="col p-3 text-left">
                    <b>Sum of weights</b><br>
                    <?php echo sprintf('%g', $sample["sum-of-weights"]) ?>
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
                        echo sprintf('%g', $sample['cross-section']), ' pb';
                      } ?>
                  </div>
                  <?php endif ?>
                  <!-- K-factor -->
                  <?php if (array_key_exists("k-factor", $sample)): ?>
                  <div class="col p-3 text-left">
                    <b>K-factor</b><br>
                    <?php echo sprintf('%g', $sample["k-factor"]) ?>
                  </div>
                  <?php endif ?>
                  <!-- Matching efficiency -->
                  <?php if (array_key_exists("matching-eff", $sample)): ?>
                  <div class="col p-3 text-left">
                    <b>Matching efficiency</b><br>
                    <?php echo sprintf('%g', $sample["matching-eff"]) ?>
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
                  <?php if (array_key_exists("description", $sample)): ?>
                  <div class="col p-3 text-left">
                    <b>Main process</b><br>
                    <?= $sample["description"] ?>
                  </div>
                  <?php endif ?>
                  <!-- Final states -->
                  <?php if (array_key_exists("comment", $sample)): ?>
                  <div class="col p-3 text-left">
                    <b>Final states / Comment</b><br>
                    <?= $sample["comment"] ?>
                  </div>
                  <?php endif ?>
                </div>
                <div class="row">
                  <!-- Number of files produced-->
                  <div class="col p-3 text-left">
                    <b>Number of files produced</b><br>
                    <?php echo number_format($sample['n-files'], 0, '.', '&thinsp;'); ?>
                  </div>
                  <!-- Number of corrupted files -->
                  <div class="col p-3 text-left">
                    <b>Number of corrupted files</b><br>
                    <?php echo number_format($sample['n-files-bad'], 0, '.', '&thinsp;'); ?>
                  </div>
                  <!-- Number of files on EOS -->
                  <div class="col p-3 text-left">
                    <b>Number of files on EOS</b><br>
                    <?php echo number_format($sample['n-files-eos'], 0, '.', '&thinsp;'); ?>
                  </div>
                  <!-- Total size -->
                  <div class="col p-3 text-left">
                    <b>Total size</b><br>
                    <?php echo number_format($sample['size'], 2, '.', '&thinsp;'); ?> GB
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

      <?php
      // echo "<pre>";
      // print_r($totalInfo);
      // echo "</pre>";
      ?>
      <div class="container mt-5">
        <table class="table">
          <thead>
            <tr>
              <th>Total statistics</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Number of samples</td>
              <td><?php echo number_format(count($samples), 0, '.', '&thinsp;'); ?></td>
            </tr>
            <tr>
              <td>Number of all events</td>
              <td><?php echo number_format($totalInfo['n-events'], 0, '.', '&thinsp;'); ?></td>
            </tr>
            <?php if (array_key_exists("sum-of-weights", $totalInfo)): ?>
            <tr>
              <td>Sum of all weights</td>
              <td><?php echo sprintf('%g', $totalInfo["sum-of-weights"]) ?></td>
            </tr>
            <?php endif ?>
            <tr>
              <td>Number of produced files</td>
              <td><?php echo number_format($totalInfo['n-files'], 0, '.', '&thinsp;'); ?></td>
            </tr>
            <tr>
              <td>Number of corrupted files</td>
              <td><?php echo number_format($totalInfo['n-files-bad'], 0, '.', '&thinsp;'); ?></td>
            </tr>
            <tr>
              <td>Number of files on EOS</td>
              <td><?php echo number_format($totalInfo['n-files-eos'], 0, '.', '&thinsp;'); ?></td>
            </tr>
            <tr>
              <td>Total size</td>
              <td><?php echo number_format($totalInfo['size'], 2, '.', '&thinsp;'); ?> GB</td>
            </tr>
            <?php if (array_key_exists('produced-by', $totalInfo)): ?>
            <tr>
              <td>Produced by</td>
              <td>
                <ul>
                  <?php foreach ($totalInfo['produced-by'] as $producer_name => $producer_count): ?>
                  <li><code><?= $producer_name ?></code>: <?php echo number_format($producer_count, 0, '.', '&thinsp;'); ?></li>
                  <?php endforeach ?>
                </ul>
              </td>
            </tr>
            <?php endif ?>
          </tbody>
        </table>
      </div>

      <script src="<?= BASE_URL ?>/js/table.js"></script>
