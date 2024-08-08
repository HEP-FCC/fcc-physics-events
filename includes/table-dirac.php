<?php
  $metadata = json_decode(file_get_contents(SAMPLEDB_PATH), true);
  $last_update = strtotime($metadata['last_update']);
  $samples = $metadata['samples'];
?>

      <p class="mt-3 mb-1 text-end text-secondary">Last update: <?= date('Y-M-d H:i T', $last_update) ?>.</p>

      <div class="mt-5 mb-5 input-group input-group-lg">
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
        <div class="row mb-2">
          <div class="col">
            <div class="sample-box focus-ring rounded"
                 tabIndex="<?= $tab_index ?>"
                 data-search-string="<?= $sample["name"] ?> <?= $sample_id ?> <?= $sample['status'] ?> <?= $sample["production-manager"] ?>">
              <div class="sample-top rounded ps-4 bg-top-<?= $sample['status'] ?>">
                <div class="row">
                  <!-- Name -->
                  <div class="col p-3 text-left">
                    <b>Name</b><br>
                    <?= $sample["name"] ?>
                  </div>
                  <!-- Sample ID -->
                  <div class="col p-3 text-left">
                    <b>Sample ID</b><br>
                    <?= $sample_id ?>
                  </div>
                  <!-- Status -->
                  <div class="col p-3 text-left">
                    <b>Status</b><br>
                    <?= $sample["status"] ?>
                  </div>
                </div>
                <div class="row">
                  <div class="col p-3 text-left">
                    <b>Cross-section</b><br>
                    <?php
                      if ($sample['cross-section'] === 'Unknown') {
                        echo 'Unknown';
                      } else if ($sample['cross-section-error'] === 'Unknown') {
                        echo number_format($sample['cross-section'], 4, '.', '\'') . " pb";
                      } else {
                        echo number_format($sample['cross-section'], 4, '.', '\'') . " &pm; " .
                             number_format($sample['cross-section-error'], 4, '.', '\'') . " pb";
                      } ?>
                  </div>
                  <div class="col p-3 text-left">
                    <b>Efficiency</b><br>
                    <?= $sample["efficiency"] ?><br>
                    <?php if ($sample["efficiency-info"] != "") {
                      echo "{$sample['efficiency-info']}";
                    } ?>
                  </div>
                  <div class="col p-3 text-left">
                    <b>Total sum of weights</b><br>
                    <?= $sample["total-sum-of-weights"] ?>
                  </div>
                </div>
              </div>
              <div class="sample-bottom rounded-bottom ps-4 bg-bottom-<?= $sample['status'] ?>">
                <div class="row">
                  <div class="col-8 p-3 text-left">
                    <b>Total number of events</b><br>
                    <?= $sample["total-number-of-events"] ?>
                  </div>
                  <div class="col-4 p-3 text-left">
                    <b>Number of events per file</b><br>
                    <?= $sample["number-of-events-per-file"] ?>
                  </div>
                </div>
                <div class="row">
                  <div class="col-8 p-3 text-left">
                    <?php if (count($sample["paths"]) > 1): ?>
                    <b>EOS Locations</b>
                    <?php else: ?>
                    <b>EOS Location</b>
                    <?php endif ?>
                    <ul>
                    <?php foreach ($sample["paths"] as $path): ?>
                      <li>
                        <span class="text-secondary">/eos/experiment/fcc/prod</span><span><?= $path?></span>
                        <div class="d-inline copy-sample-path"
                             data-path="/eos/experiment/fcc/prod<?= $path?>">
                          <svg xmlns="http://www.w3.org/2000/svg"
                               width="16"
                               height="16"
                               fill="currentColor"
                               class="bi bi-clipboard align-baseline"
                               style="margin-left: 10px;"
                               viewBox="0 0 16 16">
                            <path d="M4 1.5H3a2 2 0 0 0-2 2V14a2 2 0 0 0 2
                                     2h10a2 2 0 0 0 2-2V3.5a2 2 0 0
                                     0-2-2h-1v1h1a1 1 0 0 1 1 1V14a1 1 0 0 1-1
                                     1H3a1 1 0 0 1-1-1V3.5a1 1 0 0 1 1-1h1z"/>
                            <path d="M9.5 1a.5.5 0 0 1 .5.5v1a.5.5 0 0
                                     1-.5.5h-3a.5.5 0 0 1-.5-.5v-1a.5.5 0 0 1
                                     .5-.5zm-3-1A1.5 1.5 0 0 0 5 1.5v1A1.5 1.5
                                     0 0 0 6.5 4h3A1.5 1.5 0 0 0 11 2.5v-1A1.5
                                     1.5 0 0 0 9.5 0z"/>
                          </svg>
                          <svg xmlns="http://www.w3.org/2000/svg"
                               width="16"
                               height="16"
                               fill="currentColor"
                               class="bi bi-clipboard-check align-baseline d-none"
                               style="margin-left: 10px;"
                               viewBox="0 0 16 16">
                            <path fill-rule="evenodd"
                                  d="M10.854 7.146a.5.5 0 0 1 0 .708l-3 3a.5.5
                                     0 0 1-.708 0l-1.5-1.5a.5.5 0 1 1
                                     .708-.708L7.5 9.793l2.646-2.647a.5.5 0 0 1
                                     .708 0"/>
                            <path d="M4 1.5H3a2 2 0 0 0-2 2V14a2 2 0 0 0 2
                                     2h10a2 2 0 0 0 2-2V3.5a2 2 0 0
                                     0-2-2h-1v1h1a1 1 0 0 1 1 1V14a1 1 0 0 1-1
                                     1H3a1 1 0 0 1-1-1V3.5a1 1 0 0 1 1-1h1z"/>
                            <path d="M9.5 1a.5.5 0 0 1 .5.5v1a.5.5 0 0
                                     1-.5.5h-3a.5.5 0 0 1-.5-.5v-1a.5.5 0 0 1
                                     .5-.5zm-3-1A1.5 1.5 0 0 0 5 1.5v1A1.5 1.5
                                     0 0 0 6.5 4h3A1.5 1.5 0 0 0 11 2.5v-1A1.5
                                     1.5 0 0 0 9.5 0z"/>
                          </svg>
                        </div>
                      </li>
                    <?php endforeach ?>
                    </ul>
                  </div>
                  <div class="col-4 p-3 text-left">
                    <b>Produced by</b><br>
                    <?= $sample["production-manager"] ?>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        <?php endforeach ?>
      </div>


      <script src="<?= BASE_URL ?>/js/table-dirac.js"></script>
