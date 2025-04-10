package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"

	"github.com/docker/docker/client"
	"github.com/gin-gonic/gin"
)

func root(ctx *gin.Context) {
	ctx.JSON(http.StatusOK, gin.H{
		"message": "Container Metrics API",
	})
}

func getMetrics(ctx *gin.Context, cli *client.Client, dockerCtx context.Context, containerNames []string) {
	// Initialize a map to store the overall metrics
	overallMetrics := map[string]map[string]float64{}

	// Iterate over the container names
	for _, containerName := range containerNames {

		// Get container stats
		containerJSON, err := cli.ContainerInspect(dockerCtx, containerName)

		if err != nil || containerJSON.State.Status != "running" {
			fmt.Printf("Container %s not found or not running\n", containerName)
			// Add the metrics to the overall metrics map
			overallMetrics[containerName] = map[string]float64{
				"cpu_absolute_usage":    -1,
				"cpu_percent_usage":     -1,
				"memory_absolute_usage": -1,
				"memory_percent_usage":  -1,
				"network_input":         -1,
				"network_output":        -1,
				"disk_read":             -1,
				"disk_write":            -1,
			}
			continue
		}

		// Get the container stats
		stats, err := cli.ContainerStats(dockerCtx, containerJSON.ID, false)
		if err != nil {
			log.Fatal(err)
		}
		defer stats.Body.Close()

		// Decode the JSON
		var containerStats map[string]any
		err = json.NewDecoder(stats.Body).Decode(&containerStats)
		if err != nil {
			log.Fatal(err)
		}

		// Process the container stats
		networkInput, networkOutput := getNetworkIO(containerStats)
		diskRead, diskWrite := getDiskIO(containerStats)
		cpuAbsoluteUsage, cpuPercentUsage := getCPUStats(containerStats)
		memoryAbsoluteUsage, memoryPercentUsage := getMemoryStats(containerStats)

		// Add the metrics to the overall metrics map
		overallMetrics[containerName] = map[string]float64{
			"cpu_absolute_usage":    cpuAbsoluteUsage,
			"cpu_percent_usage":     cpuPercentUsage,
			"memory_absolute_usage": memoryAbsoluteUsage,
			"memory_percent_usage":  memoryPercentUsage,
			"network_input":         networkInput,
			"network_output":        networkOutput,
			"disk_read":             diskRead,
			"disk_write":            diskWrite,
		}
	}

	// Return the metrics
	ctx.JSON(http.StatusOK, overallMetrics)
}

func initializeRoutes(router *gin.Engine, cli *client.Client, dockerCtx context.Context) {
	// Define the root endpoint
	router.GET("/", func(ctx *gin.Context) {
		root(ctx)
	})

	// Define a GET endpoint to fetch metrics
	router.GET("/metrics", func(ctx *gin.Context) {
		containerNames := ctx.QueryArray("container_names")
		getMetrics(ctx, cli, dockerCtx, containerNames)
	})
}

func getNetworkIO(stats map[string]any) (float64, float64) {
	// Extract network statistics from the container stats
	networkStats := stats["networks"].(map[string]any)

	// Initialize input and output variables for network (in bytes)
	networkInput := 0
	networkOutput := 0

	// Calculate the total input and output bytes for all network interfaces
	for networkInterface := range networkStats {
		networkInterfaceStats := networkStats[networkInterface].(map[string]any)
		networkInput += int(networkInterfaceStats["rx_bytes"].(float64))
		networkOutput += int(networkInterfaceStats["tx_bytes"].(float64))
	}

	// Convert bytes to megabytes
	return float64(networkInput) / 1e6, float64(networkOutput) / 1e6
}

func getDiskIO(stats map[string]any) (float64, float64) {
	// Extract disk statistics from the container stats
	diskStats := stats["blkio_stats"].(map[string]any)

	// Initialize read and write variables for disk (in bytes)
	diskRead := 0
	diskWrite := 0

	// Calculate the total read and write bytes for all block devices
	for _, deviceStats := range diskStats["io_service_bytes_recursive"].([]any) {
		deviceStatsMap := deviceStats.(map[string]any)
		if deviceStatsMap["op"] == "Read" {
			diskRead += int(deviceStatsMap["value"].(float64))
		} else if deviceStatsMap["op"] == "Write" {
			diskWrite += int(deviceStatsMap["value"].(float64))
		}
	}

	// Convert bytes to megabytes
	return float64(diskRead / 1e6), float64(diskWrite / 1e6)
}

func getCPUStats(stats map[string]any) (float64, float64) {
	// Extract cpu statistics from the container stats
	cpuStats := stats["cpu_stats"].(map[string]any)
	precpuStats := stats["precpu_stats"].(map[string]any)

	// Extract cpu usage stats
	cpuUsage := cpuStats["cpu_usage"].(map[string]any)
	precpuUsage := precpuStats["cpu_usage"].(map[string]any)

	// Calculate the CPU usage delta
	cpuDelta := cpuUsage["total_usage"].(float64) - precpuUsage["total_usage"].(float64)
	systemDelta := cpuStats["system_cpu_usage"].(float64) - precpuStats["system_cpu_usage"].(float64)

	// Calculate the CPU percentage
	cpuPercent := (cpuDelta / systemDelta) * float64(len(cpuStats["cpu_usage"].(map[string]any))) * 100.0

	// Return the CPU usage and percentage
	return cpuDelta / 1e6, cpuPercent
}

func getMemoryStats(stats map[string]any) (float64, float64) {
	// Extract memory statistics from the container stats
	memoryStats := stats["memory_stats"].(map[string]any)

	// Extract usage and limit
	memoryUsage := memoryStats["usage"].(float64)
	memoryLimit := memoryStats["limit"].(float64)

	// Calculate the memory percentage
	memoryPercent := (memoryUsage / memoryLimit) * 100.0

	// Convert bytes to megabytes
	return memoryUsage / 1e6, memoryPercent
}

func main() {
	// Initialize the Gin router
	router := gin.Default()

	// Initialize the Docker client
	cli, err := client.NewClientWithOpts(client.FromEnv)
	if err != nil {
		log.Fatal("Error creating Docker client:", err)
	}
	defer cli.Close()
	dockerCtx := context.Background()

	// Initialize routes
	initializeRoutes(router, cli, dockerCtx)

	// Start the server on port 8080
	router.Run(":8080")
}

// To compile:
// CGO_ENABLED=0 go build -o monitor
