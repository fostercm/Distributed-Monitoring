package main

import (
	"context"
	"fmt"
	"os"
	"strconv"
	"strings"
	"sync"
	"time"

	"encoding/json"
	"net/http"
	"net/url"

	probing "github.com/prometheus-community/pro-bing"
	"github.com/redis/go-redis/v9"
)

var ctx = context.Background()

func writeToRedis(redisClient *redis.Client, metric string, host string, containerName string, value string, windowSize int, wg *sync.WaitGroup) {
	// Close the wait group if it is not nil
	if wg != nil {
		defer wg.Done()
	}

	// Remove port from host if present
	if strings.Contains(host, ":") {
		host = strings.Split(host, ":")[0]
	}

	if containerName != "" {
		// Get key
		key := fmt.Sprintf("metric:%s:host:%s:container:%s", metric, host, containerName)

		// Write to Redis
		redisClient.RPush(ctx, key, value)

		if redisClient.LLen(ctx, key).Val() > int64(windowSize) {
			// Remove the oldest element
			redisClient.LPop(ctx, key)
		}
	} else {
		// Get key
		key := fmt.Sprintf("metric:%s:host:%s", metric, host)

		// Write to Redis
		redisClient.RPush(ctx, key, value)

		if redisClient.LLen(ctx, key).Val() > int64(windowSize) {
			// Remove the oldest element
			redisClient.LPop(ctx, key)
		}
	}
}

func scrapeContainerMetrics(monitorHost string, containerNames []string, windowSize int, redisClient *redis.Client, overallWG *sync.WaitGroup) {
	// Close the wait group if it is not nil
	if overallWG != nil {
		defer overallWG.Done()
	}

	// Get the base URL
	baseURL := fmt.Sprintf("http://%s/metrics", monitorHost)

	// Store the container names in a parameter
	params := url.Values{}
	for _, containerName := range containerNames {
		params.Add("container_names", containerName)
	}

	// Create the URL with parameters
	fullURL := fmt.Sprintf("%s?%s", baseURL, params.Encode())

	// Make the HTTP GET request
	response, err := http.Get(fullURL)

	// Make sure the request was successful
	metrics := make(map[string]map[string]float64)
	if err != nil {
		fmt.Println("Error scraping container metrics:", err)
		// If there is an error, set the metrics to -1
		for _, containerName := range containerNames {
			metrics[containerName] = map[string]float64{
				"cpu_absolute_usage":    -1,
				"cpu_percent_usage":     -1,
				"memory_absolute_usage": -1,
				"memory_percent_usage":  -1,
				"network_input":         -1,
				"network_output":        -1,
				"disk_read":             -1,
				"disk_write":            -1,
			}
		}
	} else {
		// Decode the JSON response
		json.NewDecoder(response.Body).Decode(&metrics)
	}

	// Close the response body
	defer response.Body.Close()

	// Set up a wait group
	var wg sync.WaitGroup

	// Write the metrics to Redis
	for containerName, containerMetrics := range metrics {
		for metric, value := range containerMetrics {
			wg.Add(1)
			go writeToRedis(redisClient, metric, monitorHost, containerName, fmt.Sprintf("%f", value), windowSize, &wg)
		}
	}

	// Wait for all goroutines to finish
	wg.Wait()
}

func getNetworkLatency(monitorHost string, windowSize int, redisClient *redis.Client, overallWG *sync.WaitGroup) {
	// Close the wait group if it is not nil
	if overallWG != nil {
		defer overallWG.Done()
	}

	// Initialize the ping client
	pinger, err := probing.NewPinger(strings.Split(monitorHost, ":")[0])
	if err != nil {
		fmt.Println("Error initializing ping client:", err)
	}

	// Set the number of packets to send
	pinger.Count = 5
	pinger.Timeout = time.Second / 10

	// Send packets
	err = pinger.Run()
	var averageTime string
	if err != nil {
		fmt.Println("Error sending packets:", err)
		averageTime = "-1"

	} else {
		// Get the average time
		averageTime = fmt.Sprintf("%f", float64(pinger.Statistics().AvgRtt)/float64(time.Millisecond))
	}

	// Write the latency to Redis
	writeToRedis(redisClient, "network_latency", monitorHost, "", averageTime, windowSize, nil)
}

func main() {
	// Connect to Redis
	Address := fmt.Sprintf("%s:%s", os.Getenv("HOST"), os.Getenv("DB_PORT"))
	redisClient := redis.NewClient(&redis.Options{
		Addr: Address,
	})
	defer redisClient.Close()

	// Clear the Redis database
	err := redisClient.FlushDB(ctx).Err()
	if err != nil {
		fmt.Println("Error flushing Redis database:", err)
		return
	}

	// Get the hosts and endpoints
	rawMonitorDict := os.Getenv("ENDPOINTS")
	var monitorDict map[string][]string
	err = json.Unmarshal([]byte(rawMonitorDict), &monitorDict)
	if err != nil {
		fmt.Println("Error parsing ENDPOINTS:", err)
		return
	}

	// Get interval
	rawInterval, err := strconv.Atoi(os.Getenv("INTERVAL"))
	interval := time.Duration(rawInterval) * time.Second
	if err != nil {
		fmt.Println("Error parsing INTERVAL:", err)
		return
	}

	// Get window size
	windowSize, err := strconv.Atoi(os.Getenv("WINDOW_SIZE"))
	if err != nil {
		fmt.Println("Error parsing WINDOW_SIZE:", err)
		return
	}

	// Define waitgroup
	var wg sync.WaitGroup

	for {
		// Get current time
		start := time.Now()

		// Scrape metrics for each host
		for host, containerNames := range monitorDict {
			wg.Add(2)
			go scrapeContainerMetrics(host, containerNames, windowSize, redisClient, &wg)
			go getNetworkLatency(host, windowSize, redisClient, &wg)
		}

		// Wait for all goroutines to finish
		wg.Wait()

		// Publish redis message
		err := redisClient.Publish(ctx, "dashboard_metrics", "uploaded").Err()
		if err != nil {
			fmt.Println("Error publishing message to Redis:", err)
		}

		// Get the elapsed time
		elapsed := time.Since(start)

		// Wait for the remaining time
		if elapsed < interval {
			time.Sleep(time.Second*10 - elapsed)
		}
	}
}

// To compile:
// CGO_ENABLED=0 go build -o monitor
