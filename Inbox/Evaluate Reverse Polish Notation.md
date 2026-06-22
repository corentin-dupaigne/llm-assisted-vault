---
difficulty: medium
neetcode_section: "Stack"
struggled: false
project: neetcode-150
date_solved: 2026-06-21
tags: [leetcode, neetcode-150, stack]
---
## Initial Intuition

Mon intuition est qu'il faut iterer sur les characteres du string:
- Quand c'est un chiffre -> push sur le stack
- Quand c'est un operator 
	- si c'est un + on ajoute stack.pop() + stack.pop() et on ajoute a la variable res
	- Si c'est un * on fait res *= stack.pop()
	- Si c'est un - on fait res -= stack.pop()

On retourne res.


## My Solution

```go
func pop(stack *[]int) int {
	popped := (*stack)[len(*stack)-1]
	
	*stack = (*stack)[:len(*stack)-1]
	
	return popped
}

func evalRPN(tokens []string) int {
var stack []int

	for i := 0; i < len(tokens); i++ {
		if val, err := strconv.Atoi(tokens[i]); err == nil {
		
			stack = append(stack, val)
		
		} else {
			switch tokens[i] {
			
			case "+":
			stack = append(stack, pop(&stack) + pop(&stack))
			
			case "-":
			stack = append(stack, -pop(&stack) + pop(&stack))
			
			case "*":
			stack = append(stack, pop(&stack) * pop(&stack))
			
			case "/":
			a := pop(&stack)
			b := pop(&stack)
			stack = append(stack, b / a)
		}
	}

}

fmt.Println(stack)

return pop(&stack)

}

// Time: O(n)
// Space: O(n)

```

### Optimal Solution

```go
func evalRPN(tokens []string) int {
	stack := make([]int, 0, len(tokens))

	for _, tok := range tokens {
		if isOperator(tok) {
			// On dépile dans des locales AVANT tout calcul.
			b := stack[len(stack)-1]
			a := stack[len(stack)-2]
			stack = stack[:len(stack)-2]

			stack = append(stack, apply(tok, a, b))
		} else {
			val, err := strconv.Atoi(tok)
			if err != nil {
				panic("token invalide: " + tok) // ou retour d'erreur selon le contrat
			}
			stack = append(stack, val)
		}
	}

	return stack[0]
}

func isOperator(tok string) bool {
	return tok == "+" || tok == "-" || tok == "*" || tok == "/"
}

func apply(op string, a, b int) int {
	switch op {
	case "+":
		return a + b
	case "-":
		return a - b
	case "*":
		return a * b
	case "/":
		return a / b
	}
	panic("opérateur inconnu: " + op)
}

// Time: O(1)
// Space: O(1)

```

## Delta

Mon intuition initiale etait proche de la solution mais non fonctionelle. J'ai par la suite trouve moi meme la solution optimale. La difference entre mon intuition et la solution est que je pensais qu'il fallait directement compute a et b et ajouter a res. Alors qu'il faut en fait compute a et b puis append au stack le resultat. Puis une fois que tous les characteres.

- **Ordre d'évaluation.** Mon `-pop(&s) + pop(&s)` pour la soustraction ne marchait que parce que Go garantit l'évaluation des appels de fonction de gauche à droite. En C, C++ ou OCaml (ordre non spécifié), le signe se serait inversé de façon non déterministe selon le compilateur. Leçon : ne jamais faire dépendre la correction d'un résultat de l'ordre d'évaluation.
- **Aliasing.** `pop(&stack)` mute `stack` via pointeur, donc l'appeler _à l'intérieur_ de `append(stack, ...)` mélange lecture et écriture de la même variable dans une seule expression. Ça « marchait » par accident de structure (on ne lit jamais que le sommet, le garbage reste enterré). Fragile.
- **Le fix.** Dépiler dans des locales `a`/`b` AVANT tout calcul → aucune expression ne combine lecture et écriture de `stack` → code correct _par lecture_ et non _par analyse_, et identique dans tout langage. Bonus : `isOperator`/`apply` extraits, parsing d'erreur géré explicitement (au lieu d'utiliser l'échec d'`Atoi` comme branche de contrôle), `return stack[0]` au lieu de re-dépiler.

## Review Log

- 2026-06-21 — first solve
