<?php
  // Load the samples from the samples database
  if (!file_exists(SAMPLEDB_PATH)) {
    die('<div class="alert alert-danger" role="alert">' .
        'ERROR: The connection to the sample database can\'t be established!<br>' .
        'Please contact site administration.' .
        '</div>');
  }

  $lastUpdate = filemtime(SAMPLEDB_PATH);
  class SampleDB extends SQLite3 {
    function __construct() {
       $this->open(SAMPLEDB_PATH);
    }
  }
  $sampleDB = new SampleDB();
  if(!$sampleDB) {
    die($sampleDB->lastErrorMsg());
  }

  $queryBase = '"accelerator" = "' . $acc . '" AND ';
  $queryBase .= '"event-type" = "' . $evtType . '" AND ';
  $queryBase .= '"file-type" = "' . $fileType . '" AND ';
  if ($campaign === 'none') {
    $queryBase .= '"campaign" IS NULL;';
  } else {
    $queryBase .= '"campaign" = "' . $campaign . '";';
  }

  $samples = array();
  $totalInfo = array();

  $ret = $sampleDB->query('SELECT * FROM sample WHERE ' . $queryBase);
  if (!$ret) {
    die($sampleDB->lastErrorMsg());
  }
  while($row = $ret->fetchArray(SQLITE3_ASSOC)) {
    $samples[$row['id']] = $row;
  }

  if (count($samples) < 1) {
    die('<div class="alert alert-danger" role="alert">' .
        'ERROR: No samples found for this selection, please contact site administration!' .
        '</div>');
  }

  // Total info
  $ret = $sampleDB->query('SELECT SUM("n-events"), SUM("n-files-good"), ' .
                          'SUM("n-files-bad"), SUM("n-files-eos"), ' .
                          'SUM("size") FROM sample WHERE ' . $queryBase);
  if (!$ret) {
    die('<div class="alert alert-danger" role="alert">' .
        'ERROR: Database error occurred:<br>' .
        $sampleDB->lastErrorMsg() .
        '<br>Please contact site administration.' .
        '</div>'
    );
  }
  while($row = $ret->fetchArray(SQLITE3_ASSOC)) {
    $totalInfo['n-events'] = $row['SUM("n-events")'] ?? -1;
    $totalInfo['n-files-good'] = $row['SUM("n-files-good")'] ?? -1;
    $totalInfo['n-files-bad'] = $row['SUM("n-files-bad")'] ?? -1;
    $totalInfo['n-files-eos'] = $row['SUM("n-files-eos")'] ?? -1;
    $totalInfo['size'] = $row['SUM("size")'] ?? -1;
    break;
  }

  // Stacks
  $stacks = array();
  $ret = $sampleDB->query('SELECT * FROM stack;');
  if (!$ret) {
    die('<div class="alert alert-danger" role="alert">' .
        'ERROR: Database error occurred:<br>' .
        $sampleDB->lastErrorMsg() .
        '<br>Please contact site administration.' .
        '</div>'
    );
  }
  while($row = $ret->fetchArray(SQLITE3_ASSOC)) {
    $stacks[$row['id']] = ['name' => $row['name'], 'path' => $row['path']];
  }
  foreach ($samples as $sampleId => &$sample) {
    $sample['stack'] = $stacks[$sample['stack_id']];
    unset($sample['stack_id']);
  }
  unset($stacks);
  // print_r($stacks);

  // Producers
  $producers = array();
  $ret = $sampleDB->query('SELECT * FROM producer;');
  if (!$ret) {
    die('<div class="alert alert-danger" role="alert">' .
        'ERROR: Database error occurred:<br>' .
        $sampleDB->lastErrorMsg() .
        '<br>Please contact site administration.' .
        '</div>'
    );
  }
  while($row = $ret->fetchArray(SQLITE3_ASSOC)) {
    $producers[$row['id']] = ['username' => $row['username'],
                              'name' => $row['name']];
  }
  foreach ($samples as $sampleId => &$sample) {
    $producerSampleLinks = array();
    $ret = $sampleDB->query('SELECT * FROM producersamplelink WHERE ' .
                            '"sample_id" = "' . $sampleId . '";');
    if (!$ret) {
      die('<div class="alert alert-danger" role="alert">' .
          'ERROR: Database error occurred:<br>' .
          $sampleDB->lastErrorMsg() .
          '<br>Please contact site administration.' .
          '</div>'
      );
    }
    $sample['produced-by'] = array();
    while($row = $ret->fetchArray(SQLITE3_ASSOC)) {
      $producer = $producers[$row['producer_id']];
      $sample['produced-by'][] = ['username' => $producer['username'],
                                  'name' => $producer['name']];
    }
  }
  // print_r($producers);
  unset($producers);

  // echo "<pre>";
  // print_r($samples);
  // echo "</pre>";
?>

      <p class="mt-1 text-end text-secondary">
        Last database update: <?= date('Y-M-d H:i T', $lastUpdate) ?>.
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

      <?php $tabIndex = 0; ?>
      <div class="container">
        <?php foreach ($samples as $sampleId => $sample): ?>
        <?php $tabIndex++; ?>
        <div class="row">
          <div class="col">
            <div class="mb-2 sample-box focus-ring rounded"
                 tabIndex="<?= $tabIndex ?>"
                 data-search-string="<?= $sample['process-name'] ?> <?php if(array_key_exists("description", $sample)) echo $sample['description']; ?> <?php if(array_key_exists("comment", $sample)) echo $sample['comment']; ?>">
              <div class="sample-top rounded ps-4 bg-top-<?= $sample['status'] ?> bg-top-<?= $sample['status'] ?>-highlight">
                <div class="row">
                  <!-- Process name / Sample path -->
                  <div class="col p-3 text-left">
                    <b>Name</b><br>
                    <?= $sample["process-name"] ?>
                  </div>
                  <!-- Number of events -->
                  <div class="col-2 p-3 text-left">
                    <b>Number of events</b><br>
                    <?php echo number_format($sample['n-events'], 0, '.', '&thinsp;'); ?>
                  </div>
                  <!-- Sum of weights -->
                  <?php if (isset($sample["sum-of-weights"])): ?>
                  <div class="col-2 p-3 text-left">
                    <b>Sum of weights</b><br>
                    <?php echo sprintf('%g', $sample["sum-of-weights"]) ?>
                  </div>
                  <?php endif ?>
                </div>
                <div class="row">
                  <!-- Cross-section -->
                  <?php if (isset($sample["cross-section"])): ?>
                  <div class="col p-3 text-left">
                    <b>Cross-section</b><br>
                    <?php
                      if ($sample['cross-section'] <= 0.) {
                        echo 'Unknown';
                      } else {
                        echo sprintf('%g', $sample['cross-section']), '&nbsp;pb';
                      } ?>
                  </div>
                  <?php endif ?>
                  <!-- K-factor -->
                  <?php if (isset($sample["k-factor"])): ?>
                  <div class="col p-3 text-left">
                    <b>K-factor</b><br>
                    <?php echo sprintf('%g', $sample["k-factor"]) ?>
                  </div>
                  <?php endif ?>
                  <!-- Matching efficiency -->
                  <?php if (isset($sample["matching-eff"])): ?>
                  <div class="col p-3 text-left">
                    <b>Matching efficiency</b><br>
                    <?php echo sprintf('%g', $sample["matching-eff"]) ?>
                  </div>
                  <?php endif ?>
                  <!-- Matching parameter -->
                  <?php if (isset($sample["matching-param"])): ?>
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
                  <?php if (isset($sample["description"])): ?>
                  <div class="col p-3 text-left">
                    <b>Main process / Description</b><br>
                    <?= $sample["description"] ?>
                  </div>
                  <?php endif ?>
                  <!-- Final states -->
                  <?php if (isset($sample["comment"])): ?>
                  <div class="col p-3 text-left">
                    <b>Final states / Comment</b><br>
                    <?= $sample["comment"] ?>
                  </div>
                  <?php endif ?>
                </div>
                <div class="row">
                  <!-- Number of files produced-->
                  <div class="col p-3 text-left">
                    <b>Number of files</b><br>
                    <?php echo number_format($sample['n-files-good'], 0, '.', '&thinsp;'); ?>
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
                    <?php
                      echo number_format($sample['size'], 2, '.', '&thinsp;'), '&nbsp;GB';
                    ?>
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
                  <!-- Produced by -->
                  <?php if (count($sample['produced-by']) > 0): ?>
                  <div class="col-4 p-3 text-left">
                    <b>Produced by</b><br>
                    <?php
                      $userList = '';
                      foreach ($sample['produced-by'] as $producerIdx => $producer) {
                        if (isset($producer['name'])) {
                          $userList .= $producer['name'] . ', ';
                        } else {
                          $userList .= '<code>' . $producer['username'] . '</code>, ';
                        }
                      }
                      $userList = rtrim($userList);
                      $userList = rtrim($userList, ',');
                      echo $userList;
                    ?>
                  </div>
                  <?php endif ?>
                </div>
                <div class="row">
                  <?php if (isset($sample["stack"])): ?>
                  <div class="col p-3 text-left">
                    <b>Key4hep stack</b><br>
                    <?= $sample['stack']['path'] ?>
                  </div>
                  <?php endif ?>
                  <div class="col-2 p-3 text-left">
                    <b>Status</b><br>
                    <?php if ($sample['status'] == 'on-tape'): ?>
                    Moved to tape
                    <?php else: ?>
                    <?= $sample['status'] ?>
                    <?php endif ?>
                  </div>
                  <div class="col-2 p-3 text-left">
                    <b>Last activity</b><br>
                    <?= date('Y-M-d H:i T', strtotime($sample['last-update'])) ?>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        <?php endforeach ?>
      </div>

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
              <td>Number of files</td>
              <td><?php echo number_format($totalInfo['n-files-good'], 0, '.', '&thinsp;'); ?></td>
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
              <td>
                <?php
                  echo number_format($totalInfo['size'], 2, '.', '&thinsp;'), '&nbsp;GB';
                ?>
              </td>
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
