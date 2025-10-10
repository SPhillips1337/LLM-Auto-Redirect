<?php
// Improved bulk processing method - replace the existing one

public function handle_bulk_process_ajax() {
    check_ajax_referer('lar_ajax_nonce', 'nonce');
    
    if (!current_user_can('manage_options')) {
        wp_send_json_error('Permission denied.', 403);
    }
    
    // Set longer time limit for bulk processing
    if (function_exists('set_time_limit')) {
        set_time_limit(300); // 5 minutes
    }
    
    global $wpdb;
    $log_table = $wpdb->prefix . 'redirection_404';
    $redirect_table = $wpdb->prefix . 'redirection_items';
    
    // Get all 404s without redirects (limit to prevent timeout)
    $all_query = "SELECT DISTINCT l.url FROM {$log_table} l LEFT JOIN {$redirect_table} r ON l.url = r.url WHERE r.id IS NULL LIMIT 50";
    $all_results = $wpdb->get_results($all_query);
    
    if (empty($all_results)) {
        wp_send_json_success(['processed' => 0, 'created' => 0, 'message' => 'No 404s to process']);
    }
    
    // Filter out ignored URLs
    $urls_to_process = array_filter($all_results, function($row) {
        return !$this->should_ignore_url($row->url);
    });
    
    $processed = 0;
    $created = 0;
    $errors = [];
    
    foreach ($urls_to_process as $row) {
        try {
            // Check memory usage
            $memory_mb = memory_get_usage(true) / 1024 / 1024;
            if ($memory_mb > 400) {
                $errors[] = "Memory limit approaching ({$memory_mb}MB) - stopping bulk process";
                break;
            }
            
            $suggestion = $this->get_llm_suggestion($row->url);
            
            if ($suggestion && $suggestion !== home_url('/')) {
                // Create redirect
                if (class_exists('Red_Item')) {
                    $result = Red_Item::create([
                        'url' => $row->url,
                        'action_data' => ['url' => $suggestion],
                        'match_type' => 'url',
                        'action_type' => 'url',
                        'action_code' => 301,
                        'group_id' => 1,
                    ]);
                    
                    if ($result && !is_wp_error($result)) {
                        $wpdb->delete("{$wpdb->prefix}redirection_404", ['url' => $row->url]);
                        $created++;
                    } else {
                        $error_msg = is_wp_error($result) ? $result->get_error_message() : 'Unknown error';
                        $errors[] = "Failed to create redirect for {$row->url}: {$error_msg}";
                    }
                } else {
                    $errors[] = "Red_Item class not available";
                    break;
                }
            }
            
            $processed++;
            
            // Add small delay to prevent overwhelming the LLM
            usleep(100000); // 0.1 second
            
        } catch (Exception $e) {
            $errors[] = "Error processing {$row->url}: " . $e->getMessage();
        }
    }
    
    $response = [
        'processed' => $processed,
        'created' => $created,
        'total_found' => count($all_results),
        'filtered_count' => count($urls_to_process)
    ];
    
    if (!empty($errors)) {
        $response['errors'] = $errors;
    }
    
    wp_send_json_success($response);
}
?>
