---
difficulty: easy
neetcode_section: "Linked List"
struggled: false
project: neetcode-150
date_solved: 2026-06-30
tags: [leetcode, neetcode-150, linked-list]
---
## Initial Intuition

Mon intuition est qu'il suffisait simplement de relier la tail de la premiere linked list a la head de la deuxieme Mais les schema montrent que les list sont merges et non pas juste reliees entre elles mais je ne comprends pas les criteres permettant de definir le placement de deux nodes. Ok j'ai juste mal lu, il est clairement indique que les listes doivent etre sort.

Je pense que l'algo est de d'iterer sur les deux list en meme temps tant qu'il y a un next sur les deux, pour le current de chaque liste on prend le premier en plus petit et on l'ajoute sur la nouvelle liste (je me demande si il n'est pas possible d'utiliser une liste deja existante au lieu d'en recreer une pour economiser de l'espace). A la fin d'une liste, si reste des elements dans la deuxieme liste on les ajoutes seulement a la suite.

Il y a un probleme avec ma logique -> j'avance tout le temps les deux listes mais parfois il faudrait n'en avancer qu'une. Par exemple si j'ai une liste 10-9-8 et 2-3-4. Il ne faut avancer que la 2eme vu que la 1ere est plus grande que tous les elements de la deuxieme.


## My Solution

```go
/**
 * Definition for singly-linked list.
 * type ListNode struct {
 *     Val int
 *     Next *ListNode
 * }
 */

func mergeTwoLists(list1 *ListNode, list2 *ListNode) *ListNode {

	dummy := &ListNode{}
	curr := dummy

	for list1 != nil || list2 != nil {

		if list1 == nil {
			curr.Next = list2
			break
		} 

		if list2 == nil {
			curr.Next = list1
			break
		}

		if list1.Val < list2.Val {
			curr.Next = list1
			curr = curr.Next
			list1 = list1.Next
		} else {
			curr.Next = list2
			curr = curr.Next
			list2 = list2.Next
		}
	}

	return dummy.Next
}


// Time: O(n + m)
// Space: O(1)

```

### Optimal Solution

```go
/**
 * Definition for singly-linked list.
 * type ListNode struct {
 *     Val int
 *     Next *ListNode
 * }
 */

func mergeTwoLists(list1 *ListNode, list2 *ListNode) *ListNode {

	dummy := &ListNode{}
	curr := dummy

	for list1 != nil && list2 != nil {

		if list1.Val < list2.Val {
			curr.Next = list1
			curr = curr.Next
			list1 = list1.Next
		} else {
			curr.Next = list2
			curr = curr.Next
			list2 = list2.Next
		}
	}

		if list1 == nil {
			curr.Next = list2
		} 

		if list2 == nil {
			curr.Next = list1
		}


	return dummy.Next
}


// Time: O(m + n)
// Space: O(1)

```

## Delta

Ma complexite etait optimale mais le code pouvait etre ameliore en terme de proprete.

## Review Log

- 2026-06-30 — first solve
