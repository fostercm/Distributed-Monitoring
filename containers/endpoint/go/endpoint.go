package main

import (
	"strconv"

	"math/rand"
	"net/http"

	"github.com/gin-gonic/gin"
	"gonum.org/v1/gonum/mat"
)

func root(ctx *gin.Context) {
	ctx.JSON(http.StatusOK, gin.H{
		"message": "Sample Container API",
	})
}

func compute(ctx *gin.Context) {
	// Initialize the constants
	a, _ := strconv.Atoi(ctx.Query("a"))
	b, _ := strconv.Atoi(ctx.Query("b"))
	c, _ := strconv.Atoi(ctx.Query("c"))

	// Create 3 random arrays
	array1 := randomMatrix(a, b)
	array2 := randomMatrix(b, c)
	array3 := randomMatrix(c, a)

	// Perform matrix multiplication
	var tmp mat.Dense
	var result mat.Dense

	tmp.Mul(array1, array2)
	result.Mul(&tmp, array3)

	// Return the result
	ctx.JSON(http.StatusOK, gin.H{
		"result": "Success",
	})
}

func randomMatrix(rows int, cols int) *mat.Dense {
	// Create a random matrix of the given size
	data := make([]float64, rows*cols)
	for i := range data {
		data[i] = rand.Float64()
	}
	return mat.NewDense(rows, cols, data)
}

func initializeRoutes(router *gin.Engine) {
	// Define the routes
	router.GET("/", root)
	router.GET("/compute", compute)
}

func main() {
	// Initialize routes
	router := gin.Default()
	initializeRoutes(router)

	// Start the server
	router.Run(":8000")

}

// CGO_ENABLED=0 go build -o monitor
